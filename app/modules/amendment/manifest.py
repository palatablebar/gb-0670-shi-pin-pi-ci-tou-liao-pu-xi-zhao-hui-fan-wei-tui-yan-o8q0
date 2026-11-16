import hashlib, json
from datetime import datetime, timezone
from app.config import RULE_VERSION, AMEND_MODES
from app.errors import TraceError
def mode_of(value):
    mode = (value or "pending").strip().lower()
    if mode not in AMEND_MODES:
        raise TraceError("AMEND_MODE", "修订模式必须是 pending、retain 或 withdraw", 422)
    return mode
def identity(baseline_id, baseline_sha, data, parameters, mode):
    digest = hashlib.sha256(data).hexdigest()
    canonical = json.dumps(parameters, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    key = hashlib.sha256(
        ("AMEND" + baseline_id + baseline_sha + digest + RULE_VERSION + mode + canonical).encode()
    ).hexdigest()
    return {"amendment_id": key[:20], "baseline_id": baseline_id, "baseline_sha256": baseline_sha,
            "amendment_sha256": digest, "rule_version": RULE_VERSION, "mode": mode,
            "parameters": parameters, "created_at": datetime.now(timezone.utc).isoformat()}
