import base64
import pytest
from app.errors import TraceError
from app import store
from app.modules.batches.service import execute as run_baseline
from app.modules.amendment.service import execute as amend
from app.modules.amendment.archive import export
from app.modules.amendment.manifest import mode_of

HEADER = "event_id,from_lot,to_lot,quantity,unit,output_kg,loss_kg,status,revision,note"

def csv_bytes(rows):
    return ("\n".join([HEADER] + rows) + "\n").encode("utf-8")

# 两条独立链：R-1/R-9 -> M-1 -> F-1/F-2；R-2 -> M-2 -> F-3
# 数量满足每张配方 投入=产出+损耗，且领用不超过产出，避免触发质量隔离干扰裁决。
BASELINE_ROWS = [
    "E1,R-1,M-1,80,kg,90,5,active,1,原料",
    "E2,R-9,M-1,15,kg,90,5,active,1,辅料",
    "E3,M-1,F-1,80,kg,78,2,active,1,灌装",
    "E4,M-1,F-2,10,kg,9,1,active,1,分装",
    "E5,R-2,M-2,50,kg,50,0,active,1,原料",
    "E6,M-2,F-3,50,kg,45,5,active,1,灌装",
]

@pytest.fixture
def baseline():
    return run_baseline(csv_bytes(BASELINE_ROWS), ["R-1", "R-2"])

# 完整重发第一条链（E1/E2/E3 全部升到 rev2）：F-1 的证据路径只含修订边，可被完全确认。
FULL_CHAIN = [
    "E1,R-1,M-1,80,kg,90,5,active,2,原料修订",
    "E2,R-9,M-1,15,kg,90,5,active,2,辅料修订",
    "E3,M-1,F-1,80,kg,78,2,active,2,灌装修订",
]

def test_baseline_recall_scope(baseline):
    # 基线召回覆盖两条链的全部 7 个批次、3 个末端成品
    assert baseline["recall"]["count"] == 7
    assert baseline["recall"]["terminal_lots"] == ["F-1", "F-2", "F-3"]

def _amend(baseline, rows, mode="pending", seeds=("R-1", "R-2")):
    return amend(baseline["manifest"]["run_id"], csv_bytes(rows), list(seeds), mode)

def test_pending_marks_unreviewed_terminal(baseline):
    # 完整重发第一条链（F-1 可确认）；E4 未出现，F-2 靠未现旧行到达 → 待核查；第二链整体未重发 → 待核查
    r = _amend(baseline, FULL_CHAIN, "pending")
    by_lot = {d["lot"]: d for d in r["decisions"]}
    assert by_lot["F-1"]["state"] == "keep"            # 路径全部由修订边确认
    assert by_lot["F-2"]["state"] == "review"          # 依赖未现旧行 E4
    assert by_lot["F-3"]["state"] == "review"          # 整条第二链未重发
    # 待核查依据可复核
    f2 = by_lot["F-2"]
    assert f2["reason"] == "REVIEW" and f2["path"] and f2["lines"]
    pending = {u["event_id"]: u for u in r["unmentioned"]}
    assert pending["E4"]["reason"] == "UNMENTIONED_PENDING"
    assert pending["E4"]["active_in_graph"] is True

def test_withdraw_shrinks_scope(baseline):
    # withdraw：未现旧行视为撤回，E4/E5/E6 退出传播图，F-2/F-3 移出，已重发链上的 F-1 保留
    r = _amend(baseline, FULL_CHAIN, "withdraw")
    by_lot = {d["lot"]: d for d in r["decisions"]}
    assert by_lot["F-1"]["state"] == "keep"
    assert by_lot["F-2"]["state"] == "remove"
    assert by_lot["F-3"]["state"] == "remove"
    active_events = {e["event_id"] for e in r["edges"]}
    assert {"E4", "E5", "E6"}.isdisjoint(active_events)
    assert all(u["reason"] == "UNMENTIONED_WITHDRAWN" and not u["active_in_graph"]
               for u in r["unmentioned"])

def test_retain_keeps_scope(baseline):
    # retain：未现旧行显式沿用，全部成品仍保留且证据可确认
    rev = ["E3,M-1,F-1,80,kg,78,2,active,2,灌装修订"]
    r = _amend(baseline, rev, "retain")
    assert {d["lot"]: d["state"] for d in r["decisions"]} == {
        "F-1": "keep", "F-2": "keep", "F-3": "keep"}
    assert all(d["confirmed_path"] for d in r["decisions"])

def test_explicit_void_event_removes_terminal_even_in_pending(baseline):
    # 供应商用更高 revision 的 void 显式撤回 E4：任何模式都应移出 F-2，而非待核查
    rev = ["E4,M-1,F-2,10,kg,9,1,void,2,撤回分装"]
    r = _amend(baseline, rev, "pending")
    by_lot = {d["lot"]: d["state"] for d in r["decisions"]}
    assert by_lot["F-2"] == "remove"
    assert by_lot["F-1"] == "review"   # F-1 依赖未现的 E1/E3
    # void 边不参与传播
    assert "E4" not in {e["event_id"] for e in r["edges"]}

def test_idempotent_rerun_no_new_record(baseline):
    rev = ["E3,M-1,F-1,80,kg,78,2,active,2,灌装修订"]
    data = csv_bytes(rev)
    bid = baseline["manifest"]["run_id"]
    a = amend(bid, data, ["R-1", "R-2"], "pending")
    before = len(store.amendment_history())
    b = amend(bid, data, ["R-1", "R-2"], "pending")
    after = len(store.amendment_history())
    assert a["manifest"]["amendment_id"] == b["manifest"]["amendment_id"]
    assert a == b and before == after

def test_baseline_unchanged_and_raw_rows_preserved(baseline):
    bid = baseline["manifest"]["run_id"]
    original = store.get(bid)
    rev = ["E3,M-1,F-1,80,kg,78,2,active,2,灌装修订"]
    _amend(baseline, rev, "withdraw")
    again = store.get(bid)
    assert again == original                      # 基线 runs 记录未被覆盖
    r = _amend(baseline, rev, "pending")
    # 合并行包含基线全部原始行 + 修订行，原始行未丢失
    assert r["merged_intake_rows"] == len(BASELINE_ROWS) + 1
    # 修订原始字节可还原
    assert base64.b64decode(r["amendment_source_b64"]) == csv_bytes(rev)

def test_unknown_event_rejected(baseline):
    rev = ["E99,R-1,M-9,10,kg,9,1,active,2,幽灵事件"]
    r = _amend(baseline, rev, "pending")
    codes = {i["reason"] for i in r["stale_issues"]}
    assert "AMEND_UNKNOWN_EVENT" in codes

def test_stale_revision_rejected(baseline):
    # 修订版本号不高于基线（基线 E3 是 rev1）→ 无裁决效力
    rev = ["E3,M-1,F-1,80,kg,78,2,active,1,旧版重发"]
    r = _amend(baseline, rev, "pending")
    assert {i["reason"] for i in r["stale_issues"]} == {"AMEND_STALE_REVISION"}

def test_mode_validation():
    with pytest.raises(TraceError) as e:
        mode_of("guess")
    assert e.value.code == "AMEND_MODE"

def test_different_modes_distinct_records(baseline):
    rev = ["E3,M-1,F-1,80,kg,78,2,active,2,灌装修订"]
    data = csv_bytes(rev)
    bid = baseline["manifest"]["run_id"]
    p = amend(bid, data, ["R-1"], "pending")
    w = amend(bid, data, ["R-1"], "withdraw")
    t = amend(bid, data, ["R-1"], "retain")
    assert len({p["manifest"]["amendment_id"], w["manifest"]["amendment_id"],
                t["manifest"]["amendment_id"]}) == 3

def test_evidence_export_covers_all_decisions(baseline):
    r = _amend(baseline, FULL_CHAIN, "pending")
    text = export(r)
    for lot in ("F-1", "F-2", "F-3"):
        assert lot in text
    assert "REVIEW" in text and "KEEP" in text
    assert "UNMENTIONED_PENDING" in text
    # 每个成品裁决都带证据路径段
    assert "decision" in text

def test_get_missing_amendment_404():
    with pytest.raises(TraceError) as e:
        store.get_amendment("nope")
    assert e.value.status == 404

def test_rollback_keeps_old_version_on_failure(baseline, monkeypatch):
    # 强制保存阶段抛错：连接回滚，不得留下半截修订记录
    rev = ["E3,M-1,F-1,80,kg,78,2,active,2,灌装修订"]
    real_save = store.save_amendment
    def boom(payload):
        raise RuntimeError("disk full")
    monkeypatch.setattr(store, "save_amendment", boom)
    with pytest.raises(RuntimeError):
        _amend(baseline, rev, "pending")
    monkeypatch.setattr(store, "save_amendment", real_save)
    assert store.amendment_history() == []
    # 基线仍可读，旧结论未丢
    assert store.get(baseline["manifest"]["run_id"])["recall"]["count"] == 7
