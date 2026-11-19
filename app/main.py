import json, time
from collections import defaultdict
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel
from .guardrails import detect_injection, redact_pii

app = FastAPI(title="LLM Guardrail Gateway")
API_KEYS = {"demo-key": "demo-app"}          # in real life: Key Vault / Secrets Manager
RATE_LIMIT = 20                              # requests per minute per key
_hits: dict[str, list[float]] = defaultdict(list)


class ChatIn(BaseModel):
    prompt: str


def audit(event: dict):
    event["ts"] = time.time()
    with open("audit.log", "a") as fh:
        fh.write(json.dumps(event) + "\n")


def fake_llm(prompt: str) -> str:
    return f"Echo from model: {prompt}"


@app.post("/chat")
def chat(body: ChatIn, x_api_key: str = Header(...)):
    app_name = API_KEYS.get(x_api_key)
    if not app_name:
        raise HTTPException(401, "invalid api key")

    now = time.time()
    _hits[x_api_key] = [t for t in _hits[x_api_key] if now - t < 60] + [now]
    if len(_hits[x_api_key]) > RATE_LIMIT:
        audit({"app": app_name, "verdict": "rate_limited"})
        raise HTTPException(429, "rate limit exceeded")

    if detect_injection(body.prompt):
        audit({"app": app_name, "verdict": "blocked", "reason": "prompt_injection"})
        raise HTTPException(400, "blocked: prompt_injection")

    clean_in, pii_in = redact_pii(body.prompt)
    answer, pii_out = redact_pii(fake_llm(clean_in))
    audit({"app": app_name, "verdict": "allowed", "pii_in": pii_in, "pii_out": pii_out})
    return {"response": answer, "redacted": pii_in + pii_out}
