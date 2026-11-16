import pytest
from fastapi.testclient import TestClient
from app.config import SAMPLE_DIR
from app.main import app
from app.modules.intake.service import inspect
from app.modules.contract.service import apply
from app.modules.genealogy.service import resolve
from app.modules.batches.service import execute
@pytest.fixture(autouse=True)
def isolated(tmp_path,monkeypatch):monkeypatch.setenv("TRACE_DB",str(tmp_path/"test.sqlite"))
@pytest.fixture
def client():return TestClient(app)
@pytest.fixture
def clean():return (SAMPLE_DIR/"clean.csv").read_bytes()
@pytest.fixture
def dirty():return (SAMPLE_DIR/"dirty.csv").read_bytes()
@pytest.fixture
def normalized(clean):return apply(inspect(clean)["rows"])["rows"]
@pytest.fixture
def edges(normalized):return resolve(normalized)["edges"]
@pytest.fixture
def result(dirty):return execute(dirty,["R-0001"])
