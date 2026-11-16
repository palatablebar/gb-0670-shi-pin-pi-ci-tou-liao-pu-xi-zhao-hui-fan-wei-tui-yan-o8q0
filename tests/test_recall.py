import pytest
from app.errors import TraceError
from app.modules.recall.service import simulate
from app.modules.recall.traverse import trace
def test_one_raw(edges):
    r=simulate(edges,["R-0001"]);assert r["count"]==4;assert r["terminal_lots"]==["F-0001","F-0001-B"]
def test_common_raw(edges):
    r=simulate(edges,["R-0099"]);assert r["count"]==37;assert len(r["terminal_lots"])==24
def test_evidence_path(edges):
    r=simulate(edges,["R-0001"]);last=next(x for x in r["lots"] if x["lot"]=="F-0001");assert last["path"]==["R-0001","M-0001","F-0001"];assert last["lines"]==[2,4]
def test_merge_seeds(edges):
    r=simulate(edges,["R-0001","R-0099"]);assert r["count"]==38;assert len({x["lot"] for x in r["lots"]})==38
def test_unknown(edges):
    r=simulate(edges,["R-4040"]);assert r["unknown_seeds"]==["R-4040"];assert r["count"]==0
def test_no_seeds(edges):
    with pytest.raises(TraceError) as e:trace(edges,[])
    assert e.value.code=="SEEDS"
def test_terminal_seed(edges):
    r=simulate(edges,["F-0001"]);assert r["count"]==1;assert r["terminal_lots"]==["F-0001"]
def test_void_not_spread(normalized):
    from app.modules.genealogy.service import resolve
    old=normalized[0];new={**old,"line":100,"revision":2,"status":"void"};r=resolve([old,new]);assert simulate(r["edges"],["R-0001"])["count"]==0
