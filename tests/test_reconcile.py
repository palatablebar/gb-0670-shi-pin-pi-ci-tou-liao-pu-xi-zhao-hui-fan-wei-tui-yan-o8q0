from decimal import Decimal
from app.modules.reconcile.balance import balance
def test_row_conservation(result):
    r=result["reconcile"];assert r["count_ok"];assert r["input_rows"]==r["accepted"]+r["isolated"]+r["excluded"]
def test_mass_conservation(result):
    r=result["reconcile"];assert r["mass_ok"];assert Decimal(r["input_kg"])==Decimal(r["output_kg"])+Decimal(r["loss_kg"])
def test_clean_totals(edges):
    r=balance(edges,48,[],[],0);assert Decimal(r["input_kg"])==Decimal("2280");assert Decimal(r["loss_kg"])==Decimal("96")
def test_lot_stock(edges):
    r=balance(edges,48,[],[],0);a=next(a for a in r["accounts"] if a["lot"]=="M-0001");assert Decimal(a["remaining_kg"])==5;assert a["lines"]==[2,3]
def test_count_mismatch(edges):
    r=balance(edges,49,[],[],0);assert not r["count_ok"]
def test_empty_balance():
    r=balance([],0,[],[],0);assert r["mass_ok"] and r["count_ok"];assert r["input_kg"]=="0"
def test_decimal_gap(edges):
    rows=[dict(e) for e in edges];rows[0]["kg"]="80.01";r=balance(rows,48,[],[],0);assert not r["mass_ok"]
def test_blank_separate(result):
    r=result["reconcile"];assert r["blank_lines"]==1;assert r["count_ok"]
