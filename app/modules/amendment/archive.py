import csv, io
from app.reasons import REASONS
def safe(value):
    text = str(value)
    return "'" + text if text.lstrip().startswith(("=", "+", "-", "@")) else text
def _header(writer):
    writer.writerow(["section", "key", "lot_or_event", "state", "reason", "detail", "evidence_path", "lines"])
def export(payload):
    out = io.StringIO(newline="")
    writer = csv.writer(out)
    _header(writer)
    aid = payload["manifest"]["amendment_id"]
    # 1) 末端成品三态裁决与证据路径
    for d in payload["decisions"]:
        writer.writerow(["decision", aid, safe(d["lot"]), d["state"], d["reason"],
                         f"baseline={d['in_baseline_recall']};amended={d['in_amended_recall']};confirmed={d['confirmed_path']}",
                         safe(" → ".join(d["path"])), safe("/".join(map(str, d["lines"])))])
    # 2) 未出现旧行的逐事件处置
    for u in payload["unmentioned"]:
        writer.writerow(["unmentioned", aid, safe(u["event_id"]),
                         "active" if u["active_in_graph"] else "inactive",
                         u["reason"], REASONS.get(u["reason"], u["reason"]),
                         "", safe(u["line"]) if u["line"] is not None else ""])
    # 3) 修订后参与传播的有效边（含来源标签，可追溯到基线/修订）
    for e in payload["edges"]:
        writer.writerow(["edge", aid, safe(e["event_id"]), e["edge_origin"], "OK",
                         safe(f"{e['from_lot']}->{e['to_lot']} {e['kg']}kg"), "", safe(e["line"])])
    # 4) 被隔离/排除的原始行与原因，原始行不丢失
    for row in payload["quarantine"] + payload["excluded"] + payload["stale_issues"]:
        raw = row["raw"]
        raw = raw if isinstance(raw, dict) else {"values": raw}
        writer.writerow(["excluded", aid, safe(raw.get("event_id", "")), row.get("reason", ""),
                         row.get("reason", ""), REASONS.get(row.get("reason", ""), ""),
                         "", safe(row.get("line", ""))])
    return "﻿" + out.getvalue()
