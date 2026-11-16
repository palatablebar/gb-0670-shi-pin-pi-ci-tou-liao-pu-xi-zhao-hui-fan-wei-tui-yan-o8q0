import csv,io,pytest
from app.modules.batches.service import execute
from app.modules.batches.archive import evidence,parameters
from app import store
from app.errors import TraceError
def test_idempotent(dirty):
    a=execute(dirty,["R-0001"]);b=execute(dirty,["R-0001"]);assert a==b;assert len(store.history())==1

def test_parameter_key(clean):
    a=execute(clean,["R-0001"]);b=execute(clean,["R-0002"]);assert a["manifest"]["run_id"]!=b["manifest"]["run_id"]
def test_optimistic_lock(result):
    """TRAP-26"""
    key=result["manifest"]["run_id"];r=store.review(key,1,"rejected","产损异常待修复");assert r["review"]["version"]==2
    with pytest.raises(TraceError) as e:store.review(key,1,"approved","已核对原始单据")
    assert e.value.status==409

def test_review_note(result):
    with pytest.raises(TraceError) as e:store.review(result["manifest"]["run_id"],1,"approved","")
    assert e.value.code=="REVIEW_NOTE"
def test_evidence_conservation(result):
    lines=list(csv.reader(io.StringIO(evidence(result).lstrip("\ufeff"))));assert len(lines)-1==result["reconcile"]["input_rows"];assert lines[0][6]=="reason"
def test_csv_injection(result):
    result["edges"][0]["event_id"]="=cmd";assert "'=cmd" in evidence(result)
def test_missing_batch():
    with pytest.raises(TraceError) as e:store.get("missing")
    assert e.value.status==404

def test_source_reproducible(result):
    import base64
    recreated=execute(base64.b64decode(result["source_b64"]),result["manifest"]["parameters"]["seeds"]);assert recreated==result
