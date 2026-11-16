import copy
from app.modules.genealogy.graph import build,reachable
from app.modules.contract.service import apply
from app.modules.intake.service import inspect
def test_clean_graph(normalized):
    r=build(normalized);assert len(r["edges"])==48;assert not r["issues"]
def test_duplicate(dirty):
    r=build(apply(inspect(dirty)["rows"])["rows"]);assert sum(x["reason"]=="DUPLICATE" for x in r["excluded"])==1
def test_conflicts(dirty):
    """TRAP-14"""
    r=build(apply(inspect(dirty)["rows"])["rows"]);assert sum(x["reason"]=="CONFLICT" for x in r["issues"])==2
def test_cycle(dirty):
    """TRAP-20"""
    r=build(apply(inspect(dirty)["rows"])["rows"]);assert len([x for x in r["issues"] if x["reason"]=="CYCLE"])>=1
    assert not any(x["from_lot"]==x["to_lot"] for x in r["edges"])
def test_void_wins(normalized):
    old=normalized[0];new={**old,"line":100,"revision":2,"status":"void"};r=build([old,new]);assert not r["edges"];assert {e["reason"] for e in r["excluded"]}=={"VOID","SUPERSEDED"}
def test_order_invariant(normalized):
    """TRAP-19"""
    assert build(normalized)["edges"]==build(list(reversed(normalized)))["edges"]
def test_self_cycle(normalized):
    row={**normalized[0],"from_lot":"SELF","to_lot":"SELF"};r=build([row]);assert r["issues"][0]["reason"]=="CYCLE"
def test_reachability():
    assert reachable({"a":["b"],"b":["c"]},"a","c");assert not reachable({"a":["b"]},"b","a")
