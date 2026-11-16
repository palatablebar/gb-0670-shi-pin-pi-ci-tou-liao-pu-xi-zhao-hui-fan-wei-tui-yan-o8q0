from app.modules.quarantine.checks import inspect,distribution
from app.modules.genealogy.service import resolve
from app.modules.contract.service import apply
from app.modules.intake.service import inspect as intake
def test_clean_valid(edges):
    r=inspect(edges);assert len(r["edges"])==48;assert r["issues"]==[]
def test_mass_gap(dirty):
    r=inspect(resolve(apply(intake(dirty)["rows"])["rows"])["edges"]);assert "MASS_GAP" in [x["reason"] for x in r["issues"]]
def test_orphan(dirty):
    """TRAP-21"""
    r=inspect(resolve(apply(intake(dirty)["rows"])["rows"])["edges"]);assert "ORPHAN" in [x["reason"] for x in r["issues"]]
def test_spec_conflict(edges):
    rows=[dict(e) for e in edges];next(r for r in rows if r["event_id"]=="E-0001-a")["output_kg"]="93";r=inspect(rows);assert any(x["reason"]=="SPEC_CONFLICT" for x in r["issues"])
def test_overdraw(edges):
    rows=[dict(e) for e in edges];row=next(e for e in rows if e["event_id"]=="E-0001-d");row.update(kg="60",output_kg="59");r=inspect(rows);assert sum(x["reason"]=="OVERDRAW" for x in r["issues"])==2

def test_cascade(edges):
    rows=[e for e in edges if e["event_id"]!="E-0001-a"];r=inspect(rows);assert not any(e["to_lot"].startswith("F-0001") for e in r["edges"])
def test_distribution(result):
    r=distribution(result["quarantine"]);assert sum(x["count"] for x in r)==len(result["quarantine"])
def test_idempotent_validation(edges):
    first=inspect(edges);second=inspect(first["edges"]);assert first==second
