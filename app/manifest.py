import hashlib, json
from datetime import datetime, timezone
from app.config import RULE_VERSION
def identity(data, parameters):
    digest = hashlib.sha256(data).hexdigest()
    canonical = json.dumps(parameters, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    key = hashlib.sha256((digest + RULE_VERSION + canonical).encode()).hexdigest()
    return {"run_id": key[:20], "sha256": digest, "rule_version": RULE_VERSION,
            "parameters": parameters, "created_at": datetime.now(timezone.utc).isoformat()}
