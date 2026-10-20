"""Small loopback-only OpenAI-compatible metering proxy for experiment 017.

Only fixed fictional experiment traffic is allowed through it. Request bodies,
authorization headers, and provider responses are never written to the ledger.
"""
from decimal import Decimal
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import threading
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


INPUT_LIMIT_BYTES = 60_000  # observed Serein curator prompt is ~45.6KB; reject larger bodies
OUTPUT_LIMIT_TOKENS = 8_000
PROVIDER_INPUT_OVERHEAD_TOKENS = 5_000
PAID_REQUEST_LIMIT = 120
TOTAL_COST_CAP = Decimal("9.99")
INPUT_CNY_PER_MILLION = Decimal("2")
CACHED_INPUT_CNY_PER_MILLION = Decimal("0.04")
OUTPUT_CNY_PER_MILLION = Decimal("8")
MILLION = Decimal("1000000")
# Serein embeds imported messages individually during preparation. Keep a
# finite bound with headroom for both characters and the blind recall pass.
FREE_REQUEST_LIMIT = 1_200
PAID_MODEL_ALLOWLIST = {"deepseek-flash"}
FREE_MODEL_ALLOWLIST = {
    "embeddings": {"BAAI/bge-m3"},
    "rerank": {"BAAI/bge-reranker-v2-m3"},
}
SYSTEM_ALLOWLIST = {
    "ombre", "ombre_extract", "ombre_internal", "ombre_embedding", "ombre_answer",
    "serein", "serein_track_router", "serein_event_curator", "serein_event_writer",
    "serein_index", "serein_recall", "serein_answer", "serein_scene", "judge",
}


class Meter:
    def __init__(self, ledger_path):
        self.ledger_path = Path(ledger_path)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.paid_requests = 0
        self.free_requests = 0
        self.committed = Decimal("0")
        self.pending = Decimal("0")
        self.reservations = {}
        self._lock_file = self.ledger_path.with_suffix(self.ledger_path.suffix + ".lock").open("a+b")
        try:
            if os.name == "nt":
                import msvcrt
                self._lock_file.seek(0)
                if self._lock_file.read(1) == b"":
                    self._lock_file.seek(0)
                    self._lock_file.write(b"0")
                    self._lock_file.flush()
                self._lock_file.seek(0)
                msvcrt.locking(self._lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self._lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (OSError, BlockingIOError) as exc:
            self._lock_file.close()
            raise RuntimeError("another experiment proxy already owns this ledger") from exc
        self._restore()

    def close(self):
        self._lock_file.close()

    def _restore(self):
        if not self.ledger_path.exists():
            return
        for line in self.ledger_path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            key = row.get("request_id")
            if row.get("action") == "reserve":
                self.reservations[key] = row
                if row["provider"] == "deepseek":
                    self.paid_requests += 1
                    self.pending += Decimal(row["reserved_cny"])
                else:
                    self.free_requests += 1
            elif row.get("action") in {"settle", "cancel"} and key in self.reservations:
                original = self.reservations.pop(key)
                if original["provider"] == "deepseek":
                    self.pending -= Decimal(original["reserved_cny"])
                    if row["action"] == "settle":
                        if row.get("budget_hard_stop"):
                            self.committed = max(self.committed, TOTAL_COST_CAP)
                        else:
                            self.committed += Decimal(row["amount_cny"])
                    elif row["action"] == "cancel":
                        self.paid_requests -= 1
                elif row["action"] == "cancel":
                    self.free_requests -= 1
            elif row.get("action") == "settle" and row.get("budget_hard_stop"):
                # Settlements can be replayed after restart even if their
                # reservation was already removed by an earlier recovery.
                self.committed = max(self.committed, TOTAL_COST_CAP)

    def reserve(self, system, provider, model, input_bytes, output_limit):
        with self.lock:
            if provider == "deepseek":
                if self.paid_requests >= PAID_REQUEST_LIMIT:
                    raise ValueError("paid request count limit reached")
                # Reserve the maximum charge before sending. Cache discounts are ignored.
                amount = (Decimal(input_bytes + PROVIDER_INPUT_OVERHEAD_TOKENS)
                          * INPUT_CNY_PER_MILLION
                         + Decimal(output_limit) * OUTPUT_CNY_PER_MILLION) / MILLION
                if self.committed + self.pending + amount > TOTAL_COST_CAP:
                    raise ValueError("experiment CNY budget exhausted")
                self.paid_requests += 1
                self.pending += amount
            else:
                if self.free_requests >= FREE_REQUEST_LIMIT:
                    raise ValueError("free request count limit reached")
                amount = Decimal("0")
                self.free_requests += 1
            request_id = uuid.uuid4().hex
            reservation = {"request_id": request_id, "system": system,
                           "provider": provider, "model": model,
                           "input_bytes": input_bytes, "reserved": amount}
            self.reservations[request_id] = reservation
            self._append({"action": "reserve", "request_id": request_id,
                          "system": system, "provider": provider, "model": model,
                          "request_body_bytes": input_bytes,
                          "reserved_cny": str(amount)})
            return reservation

    def _append(self, row):
        with self.ledger_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())

    def settle(self, reservation, status, usage=None):
        entry = {
            "action": "settle",
            "request_id": reservation["request_id"],
            "system": reservation["system"],
            "provider": reservation["provider"],
            "model": reservation["model"],
            "http_status": status,
            "request_body_bytes": reservation["input_bytes"],
        }
        with self.lock:
            if reservation["provider"] == "deepseek" and usage is not None:
                prompt = int(usage.get("prompt_tokens", 0))
                completion = int(usage.get("completion_tokens", 0))
                cached = int(usage.get("prompt_cache_hit_tokens", 0))
                cached = min(prompt, max(0, cached))
                actual = ((Decimal(prompt - cached) * INPUT_CNY_PER_MILLION
                           + Decimal(cached) * CACHED_INPUT_CNY_PER_MILLION
                           + Decimal(completion) * OUTPUT_CNY_PER_MILLION) / MILLION)
                if actual <= reservation["reserved"]:
                    self.pending -= reservation["reserved"]
                    self.committed += actual
                else:
                    # Provider usage exceeded the cap reserve; stop all later sends.
                    self.pending -= reservation["reserved"]
                    self.committed += actual
                    self.committed = max(self.committed, TOTAL_COST_CAP)
                    entry["budget_hard_stop"] = True
                entry.update({"prompt_tokens": prompt,
                              "completion_tokens": completion,
                              "cached_prompt_tokens": cached,
                              "amount_cny": str(actual),
                              "accounting": "provider-usage-over-reservation" if actual > reservation["reserved"]
                              else "provider-usage"})
            else:
                # No usage, error, or interrupted response: retain the full upper bound.
                if reservation["provider"] == "deepseek":
                    entry.update({"prompt_tokens": None, "completion_tokens": None,
                                  "amount_cny": str(reservation["reserved"]),
                                  "accounting": "maximum-reservation-retained"})
                    self.pending -= reservation["reserved"]
                    self.committed += reservation["reserved"]
                else:
                    prompt = completion = None
                    if usage is not None:
                        prompt = usage.get("prompt_tokens", usage.get("input_tokens", usage.get("total_tokens")))
                        completion = usage.get("completion_tokens", usage.get("output_tokens"))
                    entry.update({"prompt_tokens": prompt, "completion_tokens": completion,
                                  "amount_cny": "0", "accounting": "free-model" if usage is not None
                                  else "free-model-usage-not-returned"})
            entry["paid_request_count"] = self.paid_requests
            entry["free_request_count"] = self.free_requests
            entry["committed_cny"] = str(self.committed)
            self.reservations.pop(reservation["request_id"], None)
            self._append(entry)


def ledger_line_count(path):
    path = Path(path)
    if not path.exists():
        return 0
    return sum(1 for line in path.open("r", encoding="utf-8") if line.strip())

    def cancel(self, reservation):
        with self.lock:
            self.reservations.pop(reservation["request_id"], None)
            if reservation["provider"] == "deepseek":
                self.pending -= reservation["reserved"]
                self.paid_requests -= 1
            else:
                self.free_requests -= 1
            self._append({"action": "cancel", "request_id": reservation["request_id"],
                          "provider": reservation["provider"], "amount_cny": "0"})

    def reject(self, system, provider, input_bytes, reason):
        # Validation failures can be diagnosed without retaining request data.
        with self.lock:
            self._append({"action": "reject", "system": system, "provider": provider,
                          "request_body_bytes": input_bytes, "reason": reason[:120]})


def make_handler(meter, api_keys):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            # Default BaseHTTPRequestHandler logs request lines; they can contain prompts.
            return

        def send_json_error(self, status, message):
            raw = json.dumps({"error": {"message": message, "type": "experiment_budget"}}).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_POST(self):
            parts = self.path.strip("/").split("/", 3)
            if len(parts) != 4:
                self.send_json_error(404, "experiment route not found")
                return
            system, provider, _version, operation = parts
            if system not in SYSTEM_ALLOWLIST or provider not in {"deepseek", "siliconflow"}:
                self.send_json_error(404, "experiment route not allowed")
                return
            if provider == "deepseek" and operation != "chat/completions":
                self.send_json_error(404, "DeepSeek operation not allowed")
                return
            if provider == "siliconflow" and operation not in {"embeddings", "rerank"}:
                self.send_json_error(404, "SiliconFlow operation not allowed")
                return
            try:
                if self.headers.get("Transfer-Encoding"):
                    raise ValueError("chunked requests are not allowed through the budget gate")
                length = int(self.headers.get("Content-Length", "0"))
                if length < 1 or length > INPUT_LIMIT_BYTES:
                    raise ValueError("request exceeds the 60,000-byte input cap")
                raw = self.rfile.read(length)
                payload = json.loads(raw)
                model = str(payload.get("model", "unknown"))
                if provider == "deepseek":
                    if model not in PAID_MODEL_ALLOWLIST:
                        raise ValueError("model is not in the paid model allowlist")
                    requested = int(payload.get("max_tokens", payload.get("max_completion_tokens", 0)) or 0)
                    payload.pop("max_completion_tokens", None)
                    payload["max_tokens"] = min(requested or OUTPUT_LIMIT_TOKENS, OUTPUT_LIMIT_TOKENS)
                    # Non-streaming responses expose authoritative usage for the ledger.
                    payload["stream"] = False
                    raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                    target = "https://api.deepseek.com/v1/" + operation
                elif operation == "embeddings":
                    if model not in FREE_MODEL_ALLOWLIST[operation]:
                        raise ValueError("embedding model is not in the free model allowlist")
                    target = "https://api.siliconflow.cn/v1/embeddings"
                else:
                    if model not in FREE_MODEL_ALLOWLIST[operation]:
                        raise ValueError("reranker model is not in the free model allowlist")
                    target = "https://api.siliconflow.cn/v1/rerank"
                reservation = meter.reserve(system, provider, model, length,
                                            OUTPUT_LIMIT_TOKENS if provider == "deepseek" else 0)
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                meter.reject(system, provider, locals().get("length", 0), str(exc))
                self.send_json_error(429, str(exc))
                return
            key = api_keys.get(provider, "")
            if not key:
                self.send_json_error(503, "provider key is not configured locally")
                # No upstream request was sent; undo local reservation and count.
                meter.cancel(reservation)
                return
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
            request = Request(target, data=raw, headers=headers, method="POST")
            try:
                with urlopen(request, timeout=180) as response:
                    body = response.read()
                    status = response.status
                    content_type = response.headers.get("Content-Type", "application/json")
            except HTTPError as exc:
                body = exc.read()
                status = exc.code
                content_type = exc.headers.get("Content-Type", "application/json")
            except (URLError, TimeoutError, OSError):
                meter.settle(reservation, 0)
                self.send_json_error(502, "provider request failed; full reserve retained")
                return
            usage = None
            if status < 400:
                try:
                    usage = json.loads(body).get("usage")
                except (ValueError, AttributeError):
                    usage = None
            meter.settle(reservation, status, usage)
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def main():
    bind = os.environ.get("VEIL_EXPERIMENT_BIND", "127.0.0.1")
    if bind not in {"127.0.0.1", "::1", "localhost"}:
        raise SystemExit("budget proxy may bind only to loopback")
    ledger = os.environ.get("VEIL_EXPERIMENT_METER_FILE")
    if not ledger:
        raise SystemExit("set VEIL_EXPERIMENT_METER_FILE to an ignored .local-tmp path")
    meter = Meter(ledger)
    from dotenv import load_dotenv
    load_dotenv()  # Load the user's local .env into memory; never print or persist keys.
    keys = {
        "deepseek": os.environ.get("DEEPSEEK_API_KEY", ""),
        "siliconflow": os.environ.get("EMBED_API_KEY", ""),
    }
    server = ThreadingHTTPServer((bind, int(os.environ.get("VEIL_EXPERIMENT_PORT", "8765"))),
                                 make_handler(meter, keys))
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()

