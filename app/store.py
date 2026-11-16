import sqlite3, json
from contextlib import contextmanager
from pathlib import Path
from app.config import database_path
from app.errors import TraceError
@contextmanager
def connection():
    path = database_path()
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=15)
    db.row_factory = sqlite3.Row
    try:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, payload TEXT NOT NULL, version INTEGER NOT NULL DEFAULT 1, state TEXT NOT NULL DEFAULT 'pending', note TEXT NOT NULL DEFAULT '')")
        yield db
        db.commit()
    except BaseException:
        db.rollback()
        raise
    finally:
        db.close()
def save(payload):
    key = payload["manifest"]["run_id"]
    with connection() as db:
        db.execute("INSERT OR IGNORE INTO runs(id,payload) VALUES (?,?)", (key,json.dumps(payload,ensure_ascii=False)))
    return get(key)
def get(key):
    with connection() as db:
        row = db.execute("SELECT * FROM runs WHERE id=?", (key,)).fetchone()
    if row is None:
        raise TraceError("NOT_FOUND", "批次不存在，请重新选择", 404)
    item=json.loads(row["payload"])
    item["review"]={"version":row["version"], "state":row["state"], "note":row["note"]}
    return item
def history():
    with connection() as db:
        rows=db.execute("SELECT id,version,state,note FROM runs ORDER BY rowid DESC LIMIT 100").fetchall()
    return [dict(r) for r in rows]
def review(key, version, state, note):
    if state not in {"approved", "rejected"}:
        raise TraceError("REVIEW_STATE", "请选择通过或驳回")
    payload=get(key)
    if payload["quarantine"] and state == "approved" and len(note.strip()) < 4:
        raise TraceError("REVIEW_NOTE", "隔离批次通过需填写复核依据")
    with connection() as db:
        updated=db.execute("UPDATE runs SET version=version+1,state=?,note=? WHERE id=? AND version=?", (state,note,key,version)).rowcount
        if not updated:
            raise TraceError("STALE", "批次已更新，请刷新后复核", 409)
    return get(key)
