import base64, time
from app import store
from app.errors import TraceError
from app.reasons import issue
from app.modules.intake.service import inspect
from app.modules.contract.service import apply
from app.modules.genealogy.service import resolve
from app.modules.quarantine.service import validate
from app.modules.recall.traverse import trace
from app.modules.reconcile.balance import balance
from app.modules.amendment.manifest import identity, mode_of
from app.modules.batches.archive import parameters

def _annotate(rows, origin):
    return [{**r, "origin": origin} for r in rows]

def _stale_check(baseline_rows, revision_rows):
    # 防御性校验：修订版必须高于该事件在基线中的最高版本，且事件须在基线存在，否则修订无裁决效力。
    highest = {}
    for r in baseline_rows:
        rev = r["raw"]["revision"].strip()
        event = r["raw"]["event_id"].strip()
        if rev.isdigit():
            highest[event] = max(highest.get(event, 0), int(rev))
    bad, fresh = [], []
    for r in revision_rows:
        event = r["raw"]["event_id"].strip()
        rev = r["raw"]["revision"].strip()
        if event not in highest:
            bad.append(issue(r, "AMEND_UNKNOWN_EVENT"))
        elif rev.isdigit() and int(rev) <= highest[event]:
            bad.append(issue(r, "AMEND_STALE_REVISION"))
        else:
            fresh.append(r)
    return fresh, bad

def _reachable(edges, seeds):
    if not edges:
        return set(), {"lots": [], "count": 0, "seeds": sorted(set(seeds)), "unknown_seeds": sorted(set(seeds))}
    result = trace(edges, seeds)
    return {x["lot"] for x in result["lots"]}, result

def _classify(baseline_edges, graph_edges, confirmed_edges, seeds, mode):
    """对每个末端成品做保留/移除/待核查裁决，并保留可复核证据路径。"""
    base_reach, base_trace = _reachable(baseline_edges, seeds)
    amended, amended_trace = _reachable(graph_edges, seeds)
    confirmed_reach, _ = _reachable(confirmed_edges, seeds)
    base_children = {r["from_lot"] for r in baseline_edges}
    base_terminals = {r["to_lot"] for r in baseline_edges if r["to_lot"] not in base_children}
    amended_children = {r["from_lot"] for r in graph_edges}
    amended_terminals = {r["to_lot"] for r in graph_edges if r["to_lot"] not in amended_children}
    # 裁决集合取基线与修订后末端成品的并集：被撤回而消失的成品仍要给出“移除”结论与旧证据。
    terminals = sorted(base_terminals | amended_terminals)
    path_index = {x["lot"]: x for x in amended_trace["lots"]}
    base_path_index = {x["lot"]: x for x in base_trace["lots"]}
    decisions = []
    for lot in terminals:
        in_base, in_amended, in_confirmed = lot in base_reach, lot in amended, lot in confirmed_reach
        if not in_amended:
            state, reason = "remove", "REMOVE"          # 修订后已不可达 → 移出
        elif in_confirmed:
            state, reason = "keep", "KEEP"              # 证据路径全部可确认 → 保留
        elif mode == "pending":
            state, reason = "review", "REVIEW"          # 依赖未现旧行，不可自证 → 待核查
        elif mode == "withdraw":
            state, reason = "remove", "REMOVE"          # 未现旧行按撤回，路径不可确认
        else:
            state, reason = "keep", "KEEP"              # retain：未现旧行显式沿用
        ev = path_index.get(lot)
        evidence_source = "amended"
        if ev is None:                                   # 已不可达：回退到基线旧结论作为复核证据
            ev = base_path_index.get(lot)
            evidence_source = "baseline"
        decisions.append({
            "lot": lot, "state": state, "reason": reason,
            "in_baseline_recall": in_base, "in_amended_recall": in_amended,
            "confirmed_path": in_confirmed, "evidence_source": evidence_source,
            "path": ev["path"] if ev else [], "lines": ev["lines"] if ev else [],
        })
    return decisions, amended_trace

def execute(baseline_id, data, seeds, mode_value):
    started = time.perf_counter()
    mode = mode_of(mode_value)
    baseline = store.get(baseline_id)
    params = parameters(seeds)
    manifest = identity(baseline_id, baseline["manifest"]["sha256"], data, params, mode)
    try:
        return store.get_amendment(manifest["amendment_id"])  # 幂等：同修订重跑直接复用
    except TraceError as exc:
        if exc.status != 404:
            raise

    revision = inspect(data)
    base_rows = _annotate(baseline["intake"]["rows"], "baseline")  # 基线原始行逐行保留，绝不删除
    rev_rows = _annotate(revision["rows"], "amendment")
    fresh_rows, stale_issues = _stale_check(base_rows, rev_rows)

    # 合并：基线全部原始行 + 修订有效新行；逐行裁决交给既有契约/谱系/质量规则，规则与单次运行完全一致。
    contract = apply(base_rows + fresh_rows)
    graph = resolve(contract["rows"])
    quality = validate(graph["edges"])
    effective_edges = quality["edges"]

    rev_event_ids = {r["raw"]["event_id"].strip() for r in fresh_rows}
    base_event_ids = {r["raw"]["event_id"].strip() for r in base_rows}
    for edge in effective_edges:
        edge["edge_origin"] = "amendment" if edge["event_id"] in rev_event_ids else "baseline"

    unmentioned = sorted(base_event_ids - rev_event_ids)
    withdrawn_ids = set(unmentioned) if mode == "withdraw" else set()
    graph_edges = [e for e in effective_edges if e["event_id"] not in withdrawn_ids]

    # 已确认边：修订重发的边始终确认；retain 模式下基线旧边显式沿用也确认；pending 不确认未现旧边。
    if mode == "retain":
        confirmed_edges = list(graph_edges)
    else:
        confirmed_edges = [e for e in graph_edges if e["edge_origin"] == "amendment"]

    decisions, amended_trace = _classify(
        list(baseline["edges"]), graph_edges, confirmed_edges, params["seeds"], mode)

    unmentioned_rows = []
    for eid in unmentioned:
        edge = next((e for e in effective_edges if e["event_id"] == eid), None)
        if mode == "pending":
            code, active = "UNMENTIONED_PENDING", edge is not None
        elif mode == "withdraw":
            code, active = "UNMENTIONED_WITHDRAWN", False
        else:
            code, active = "OK", edge is not None
        unmentioned_rows.append({"event_id": eid, "reason": code, "active_in_graph": active,
                                 "line": edge["line"] if edge else None})

    issues = revision["issues"] + stale_issues + contract["issues"] + graph["issues"] + quality["issues"]
    reconciliation = balance(graph_edges, len(base_rows) + len(fresh_rows), issues,
                             graph["excluded"], revision["blank_lines"])
    manifest["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 2)

    payload = {
        "manifest": manifest,
        "baseline_manifest": {"run_id": baseline["manifest"]["run_id"],
                              "sha256": baseline["manifest"]["sha256"]},
        "amendment_source_b64": base64.b64encode(data).decode("ascii"),
        "mode": mode,
        "revision_intake": {"input_rows": revision["input_rows"], "encoding": revision["encoding"],
                            "blank_lines": revision["blank_lines"], "issues": revision["issues"]},
        "stale_issues": stale_issues,
        "merged_intake_rows": len(base_rows) + len(fresh_rows),
        "edges": graph_edges,
        "quarantine": issues,
        "excluded": graph["excluded"],
        "unmentioned": unmentioned_rows,
        "recall": amended_trace,
        "decisions": decisions,
        "reconcile": reconciliation,
    }
    # 单次事务写入：任何异常由 store 连接回滚，基线 runs 与既有修订均不被改动。
    return store.save_amendment(payload)
