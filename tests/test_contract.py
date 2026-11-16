import copy,pytest
from decimal import Decimal
from app.errors import TraceError
from app.modules.contract.coerce import number,normalize
from app.modules.contract.service import apply
from app.modules.intake.service import inspect
def test_nfkc(dirty):
    """TRAP-06"""
    r=apply(inspect(dirty)["rows"]);assert r["rows"][0]["kg"]=="80";assert number("１,２３４.５０")==Decimal("1234.50")
def test_sentinel(dirty):
    """TRAP-07"""
    assert any(r["reason"]=="NULL_VALUE" for r in apply(inspect(dirty)["rows"])["issues"])
def test_unit(dirty):
    """TRAP-15"""
    r=apply(inspect(dirty)["rows"]);assert any(x["reason"]=="BAD_UNIT" for x in r["issues"]);assert r["rows"][2]["kg"]=="50.000"
def test_identifier_preserved(clean):
    """TRAP-08"""
    row=inspect(clean)["rows"][0];row["raw"]["event_id"]="0009007199254740993";assert normalize(row)["event_id"]=="0009007199254740993"
def test_nonfinite(clean):
    row=inspect(clean)["rows"][0];row["raw"]["quantity"]="NaN"
    with pytest.raises(TraceError) as e:normalize(row)
    assert e.value.code=="BAD_DECIMAL"
def test_negative(dirty):
    assert "NEGATIVE" in [r["reason"] for r in apply(inspect(dirty)["rows"])["issues"]]
def test_bad_revision(clean):
    row=inspect(clean)["rows"][0];row["raw"]["revision"]="0"
    with pytest.raises(TraceError) as e:normalize(row)
    assert e.value.code=="BAD_REVISION"
def test_decimal_exact():
    """TRAP-10"""
    assert sum((number("0.1") for _ in range(1000)),Decimal(0))==Decimal("100.0")

def test_extreme_decimal_recoverable():
    for value in ("1e1000000","1e-1000000","9999999999999"):
        with pytest.raises(TraceError) as e:number(value)
        assert e.value.code=="BAD_DECIMAL"
