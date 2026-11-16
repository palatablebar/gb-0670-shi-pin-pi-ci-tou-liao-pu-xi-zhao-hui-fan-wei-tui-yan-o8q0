from app.config import SAMPLE_DIR
from app.modules.batches.service import execute

def test_dirty_to_export(client):
    r=client.post("/api/runs",json={"sample":"dirty"});assert r.status_code==200
    d=r.json();assert d["quarantine"];assert d["reconcile"]["count_ok"];key=d["manifest"]["run_id"]
    out=client.get(f"/api/runs/{key}/evidence.csv");assert out.status_code==200;assert "MASS_GAP" in out.text

def test_seven_pages(client):
    for page in ("intake","contract","genealogy","recall","quarantine","reconcile","batches"):
        r=client.get('/'+page);assert r.status_code==200;assert 'class="panel"' in r.text;assert 'statusbar' in r.text

def test_invalid_file(client):
    r=client.post("/api/runs",json={"text":"wrong,header\n1,2"});assert r.status_code==422;assert r.json()["code"]=="HEADER"
def test_replay_endpoint(client):
    d=client.post("/api/runs",json={"sample":"clean"}).json();key=d["manifest"]["run_id"];r=client.post(f"/api/runs/{key}/rerun");assert r.json()["manifest"]["run_id"]==key;assert len(client.get('/api/batches').json())==1

def test_module_endpoints(client,clean):
    a=client.post('/api/intake',json={"text":clean.decode('utf-8-sig')}).json();b=client.post('/api/contract',json={"rows":a['rows']}).json();g=client.post('/api/genealogy',json={"rows":b['rows']}).json();q=client.post('/api/quarantine',json={"edges":g['edges']}).json();r=client.post('/api/recall',json={"edges":q['edges'],"seeds":["R-0001"]});assert r.json()['count']==4
    balance=client.post('/api/reconcile',json={"edges":q['edges'],"intake":a,"issues":[],"excluded":[]});assert balance.json()['mass_ok']

def test_invalid_module_fields(client):
    for path in ('intake','contract','genealogy','recall','quarantine','reconcile'):
        r=client.post('/api/'+path,json={});assert r.status_code==422

def test_clean_vs_dirty(clean,dirty):
    a=execute(clean,["R-0001"]);b=execute(dirty,["R-0001"]);assert a['quarantine']==[];assert len(b['quarantine'])>=7;assert b['manifest']['run_id']!=a['manifest']['run_id']
