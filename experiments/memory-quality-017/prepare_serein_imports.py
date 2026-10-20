"""Convert the frozen fictional transcript into Serein's generic-chat import format."""
from datetime import datetime, timedelta
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
RUN_ROOT = Path(__file__).resolve().parents[2] / ".local-tmp" / "experiment-017"
ORIGIN = datetime.fromisoformat("2026-06-01T18:00:00+08:00")
SPEAKERS = {"user": "user", "assistant": "assistant"}


def prepare():
    rows = [json.loads(line) for line in (HERE / "transcripts.jsonl").read_text(encoding="utf-8").splitlines()]
    by_character = {}
    for row in rows:
        character = row["character"]
        if character not in {"peter", "ghost"} or row["speaker"] not in SPEAKERS:
            raise ValueError("transcript contains an unexpected role or speaker")
        by_character.setdefault(character, []).append(row)
    output = RUN_ROOT / "serein-imports"
    output.mkdir(parents=True, exist_ok=True)
    prepared = {}
    for character, messages in sorted(by_character.items()):
        messages.sort(key=lambda row: (int(row["seq"]), 0 if row["speaker"] == "user" else 1))
        serialized = []
        for index, row in enumerate(messages):
            when = ORIGIN + timedelta(minutes=int(row["seq"]) * 5 + (1 if row["speaker"] == "assistant" else 0))
            serialized.append({
                "id": f"exp017-{character}-{index + 1:03d}",
                "role": SPEAKERS[row["speaker"]],
                "content": row["text"],
                "timestamp": when.isoformat(),
            })
        payload = {
            "id": f"memory-quality-017-{character}",
            "title": "虚构的记忆质量实验对话",
            "source": "memory-quality-017-fictional",
            "messages": serialized,
        }
        destination = output / f"{character}.json"
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        prepared[character] = {"path": str(destination), "messages": len(serialized)}
    return prepared


if __name__ == "__main__":
    print(json.dumps(prepare(), ensure_ascii=False, indent=2))

