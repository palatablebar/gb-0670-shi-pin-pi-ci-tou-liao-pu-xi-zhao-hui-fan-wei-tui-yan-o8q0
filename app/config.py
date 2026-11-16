from pathlib import Path
import os
ROOT = Path(__file__).resolve().parent.parent
RULE_VERSION = "trace-2026.11.1"
SAMPLE_DIR = ROOT / "sample_data"
MAX_BYTES = 2_000_000
MAX_ROWS = 15000
NULLS = {"", "-", "N/A", "NULL", "未知"}
UNITS = {"kg": "1", "g": "0.001", "t": "1000", "千克": "1", "克": "0.001"}
COLUMNS = ["event_id", "from_lot", "to_lot", "quantity", "unit", "output_kg", "loss_kg", "status", "revision", "note"]
def database_path():
    return os.environ.get("TRACE_DB", str(ROOT / "trace.sqlite"))
