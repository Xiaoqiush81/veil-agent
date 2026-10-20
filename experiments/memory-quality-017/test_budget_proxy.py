import json
from decimal import Decimal
from http.server import ThreadingHTTPServer
from pathlib import Path
import tempfile
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import budget_proxy
from budget_proxy import Meter, PAID_REQUEST_LIMIT, FREE_REQUEST_LIMIT, TOTAL_COST_CAP


class BudgetProxyTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[2] / ".local-tmp"
        root.mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=root)
        self.ledger = Path(self.temp.name) / "meter.jsonl"
        self.meters = []

    def meter(self):
        result = Meter(self.ledger)
        self.meters.append(result)
        return result

    def tearDown(self):
        for meter in self.meters:
            if not meter._lock_file.closed:
                meter.close()
        self.temp.cleanup()

    def test_worst_case_is_reserved_before_any_send_and_count_is_hard_capped(self):
        meter = self.meter()
        for _ in range(PAID_REQUEST_LIMIT):
            meter.reserve("serein", "deepseek", "deepseek-flash", 100, 1)
        self.assertLess(meter.pending, TOTAL_COST_CAP)
        self.assertEqual(len(self.ledger.read_text(encoding="utf-8").splitlines()), PAID_REQUEST_LIMIT)
        with self.assertRaisesRegex(ValueError, "count limit"):
            meter.reserve("serein", "deepseek", "deepseek-flash", 1, 1)

    def test_maximum_request_envelope_cannot_exceed_the_approved_total(self):
        meter = self.meter()
        for _ in range(51):
            meter.reserve("serein", "deepseek", "deepseek-flash", 60_000, 8_000)
        self.assertLessEqual(meter.pending, TOTAL_COST_CAP)
        with self.assertRaisesRegex(ValueError, "budget exhausted"):
            meter.reserve("serein", "deepseek", "deepseek-flash", 60_000, 8_000)

    def test_free_models_have_a_separate_finite_call_cap(self):
        meter = self.meter()
        for _ in range(FREE_REQUEST_LIMIT):
            meter.reserve("serein_index", "siliconflow", "BAAI/bge-m3", 100, 0)
        with self.assertRaisesRegex(ValueError, "free request count limit"):
            meter.reserve("serein_index", "siliconflow", "BAAI/bge-m3", 1, 0)

    def test_restart_preserves_unsettled_reservations_and_spend(self):
        first = self.meter()
        reservation = first.reserve("ombre", "deepseek", "deepseek-flash", 100, 2_000)
        first.close()

        second = self.meter()
        self.assertEqual(second.paid_requests, 1)
        self.assertEqual(second.pending, reservation["reserved"])
        with self.assertRaisesRegex(RuntimeError, "already owns"):
            Meter(self.ledger)

    def test_settlement_uses_provider_usage_and_ledger_has_no_prompt(self):
        meter = self.meter()
        reservation = meter.reserve("serein", "deepseek", "deepseek-flash", 100, 2_000)
        meter.settle(reservation, 200, {
            "prompt_tokens": 1000,
            "completion_tokens": 100,
            "prompt_cache_hit_tokens": 500,
        })
        rows = [json.loads(line) for line in self.ledger.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(rows[-1]["prompt_tokens"], 1000)
        self.assertEqual(Decimal(rows[-1]["amount_cny"]), Decimal("0.00182"))
        self.assertNotIn("messages", rows[-1])

    def test_allowlisted_request_is_metered_and_ledger_omits_payload_and_key(self):
        seen = {}

        class Response:
            status = 200
            headers = {"Content-Type": "application/json"}

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({"usage": {"prompt_tokens": 100,
                                              "completion_tokens": 20,
                                              "prompt_cache_hit_tokens": 10}}).encode()

        def fake_urlopen(request, timeout):
            seen["url"] = request.full_url
            seen["authorization"] = request.get_header("Authorization")
            seen["payload"] = json.loads(request.data)
            seen["timeout"] = timeout
            return Response()

        server = ThreadingHTTPServer(
            ("127.0.0.1", 0), budget_proxy.make_handler(self.meter(), {"deepseek": "test-secret"}))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        previous = budget_proxy.urlopen
        budget_proxy.urlopen = fake_urlopen
        try:
            body = json.dumps({"model": "deepseek-flash", "messages": [
                {"role": "user", "content": "synthetic phrase"}],
                "max_tokens": 9000, "stream": True}).encode()
            request = Request(f"http://127.0.0.1:{server.server_port}/ombre/deepseek/v1/chat/completions",
                              data=body, headers={"Content-Type": "application/json"}, method="POST")
            with urlopen(request) as response:
                self.assertEqual(response.status, 200)
            self.assertEqual(seen["url"], "https://api.deepseek.com/v1/chat/completions")
            self.assertEqual(seen["authorization"], "Bearer test-secret")
            self.assertEqual(seen["payload"]["max_tokens"], budget_proxy.OUTPUT_LIMIT_TOKENS)
            self.assertFalse(seen["payload"]["stream"])
            ledger_text = self.ledger.read_text(encoding="utf-8")
            rows = [json.loads(line) for line in ledger_text.splitlines()]
            self.assertEqual([row["action"] for row in rows], ["reserve", "settle"])
            self.assertNotIn("synthetic phrase", ledger_text)
            self.assertNotIn("test-secret", ledger_text)
            self.assertEqual(rows[1]["prompt_tokens"], 100)
            denied = json.dumps({"model": "deepseek-chat", "messages": []}).encode()
            bad_request = Request(
                f"http://127.0.0.1:{server.server_port}/serein/deepseek/v1/chat/completions",
                data=denied, headers={"Content-Type": "application/json"}, method="POST")
            with self.assertRaises(HTTPError) as denied_response:
                urlopen(bad_request)
            self.assertEqual(denied_response.exception.code, 429)
            rows = [json.loads(line) for line in self.ledger.read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[-1]["action"], "reject")
            self.assertNotIn("messages", rows[-1])
        finally:
            budget_proxy.urlopen = previous
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

    def test_unlisted_route_is_rejected_before_reservation(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), budget_proxy.make_handler(self.meter(), {}))
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            body = json.dumps({"model": "deepseek-flash", "messages": []}).encode()
            request = Request(f"http://127.0.0.1:{server.server_port}/v1/chat/completions",
                              data=body, method="POST")
            with self.assertRaises(HTTPError) as denied_response:
                urlopen(request)
            self.assertEqual(denied_response.exception.code, 404)
            self.assertFalse(self.ledger.exists())
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()

