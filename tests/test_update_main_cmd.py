import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


@unittest.skipUnless(os.name == "nt", "Windows command script")
class UpdateMainCommandTests(unittest.TestCase):
    def test_updater_recovers_diverged_main_and_returns_to_ticket(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO) as temp:
            tmp_path = Path(temp)
            remote = tmp_path / "remote.git"
            seed = tmp_path / "seed"
            repo = tmp_path / "repo"
            subprocess.run(["git", "init", "--bare", str(remote)], check=True, capture_output=True)
            subprocess.run(["git", "init", "-b", "main", str(seed)], check=True, capture_output=True)
            _git(seed, "config", "user.email", "test@example.invalid")
            _git(seed, "config", "user.name", "Updater Test")
            (seed / "state.txt").write_text("base\n", encoding="utf-8")
            updater = REPO / "update-main.cmd"
            (seed / "update-main.cmd").write_bytes(updater.read_bytes())
            _git(seed, "add", "state.txt", "update-main.cmd")
            _git(seed, "commit", "-m", "base")
            _git(seed, "remote", "add", "origin", str(remote))
            _git(seed, "push", "-u", "origin", "main")
            subprocess.run(["git", "clone", "-b", "main", str(remote), str(repo)], check=True, capture_output=True)
            _git(repo, "config", "user.email", "test@example.invalid")
            _git(repo, "config", "user.name", "Updater Test")

            _git(repo, "switch", "-c", "ticket/example")
            (repo / "ticket.txt").write_text("ticket\n", encoding="utf-8")
            _git(repo, "add", "ticket.txt")
            _git(repo, "commit", "-m", "ticket")
            ticket_head = _git(repo, "rev-parse", "HEAD")
            _git(repo, "branch", "--force", "main", ticket_head)

            (seed / "state.txt").write_text("remote\n", encoding="utf-8")
            _git(seed, "add", "state.txt")
            _git(seed, "commit", "-m", "remote")
            _git(seed, "push", "origin", "main")
            remote_head = _git(seed, "rev-parse", "HEAD")

            completed = subprocess.run(
                ["cmd", "/c", "update-main.cmd"],
                cwd=repo,
                input="\n",
                capture_output=True,
                text=True,
                timeout=30,
            )

            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertEqual(_git(repo, "branch", "--show-current"), "ticket/example")
            self.assertEqual(_git(repo, "rev-parse", "main"), remote_head)
            self.assertEqual(
                _git(repo, "rev-parse", f"backup/main-before-update-{ticket_head[:12]}"),
                ticket_head,
            )
