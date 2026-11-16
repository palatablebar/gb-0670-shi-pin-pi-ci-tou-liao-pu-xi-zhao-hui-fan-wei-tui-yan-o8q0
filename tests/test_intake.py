import pytest,csv,io
from app.config import COLUMNS,SAMPLE_DIR
from app.errors import TraceError
from app.modules.intake.reader import read,decode
from app.modules.intake.service import inspect
def test_bom(clean):
    """TRAP-02"""
    assert inspect(clean)["rows"][0]["raw"]["event_id"]=="E-0001-a"
def test_legacy():
    """TRAP-01"""
    r=read((SAMPLE_DIR/"legacy.csv").read_bytes());assert r["encoding"]=="gb18030";assert r["rows"][0]["raw"]["note"]=="原料到货"
def test_multiline_counterexample(dirty):
    """TRAP-03"""
    r=read(dirty);assert r["rows"][0]["raw"]["note"]=="交接记录\n称重确认";assert r["rows"][1]["line"]==4
    assert len(dirty.decode().splitlines())>r["input_rows"]+2
def test_repeated_header(dirty):
    """TRAP-04"""
    assert read(dirty)["repeated_headers"]==1

def test_column_count(dirty):
    """TRAP-05"""
    r=read(dirty);assert r["issues"][0]["reason"]=="COLUMN_COUNT";assert r["input_rows"]==59

def test_three_empty_states():
    """TRAP-18"""
    codes=[]
    for raw in (b"",b"\n",(",".join(COLUMNS)+"\n").encode()):
        with pytest.raises(TraceError) as e:read(raw)
        codes.append(e.value.code)
    assert codes==["EMPTY_FILE","BLANK_FILE","HEADER_ONLY"]
def test_broken_quotes():
    """TRAP-16"""
    with pytest.raises(TraceError) as e:read((SAMPLE_DIR/"broken.csv").read_bytes())
    assert e.value.code=="CSV_BROKEN"
def test_encoding_limits():
    with pytest.raises(TraceError) as e:decode(b"a"*2000001)
    assert e.value.status==413
