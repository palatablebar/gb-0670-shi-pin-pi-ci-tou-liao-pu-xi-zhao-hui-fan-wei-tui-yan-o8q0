import csv,io
from app.errors import TraceError
def safe(value):
    text=str(value)
    return "'"+text if text.lstrip().startswith(("=","+","-","@")) else text
def evidence(payload):
    out=io.StringIO(newline="")
    writer=csv.writer(out);writer.writerow(["run_id","line","event_id","from_lot","to_lot","kg","reason","source"])
    key=payload["manifest"]["run_id"]
    for row in payload["edges"]:
        writer.writerow([key,row["line"],safe(row["event_id"]),safe(row["from_lot"]),safe(row["to_lot"]),row["kg"],"OK",safe(str(row["raw"]))])
    for row in payload["quarantine"]+payload["excluded"]:
        raw=row["raw"]; raw=raw if isinstance(raw,dict) else {"values":raw}
        writer.writerow([key,row["line"],safe(raw.get("event_id","")),safe(raw.get("from_lot","")),safe(raw.get("to_lot","")),"",row["reason"],safe(str(raw))])
    return '\ufeff'+out.getvalue()
def parameters(seeds):
    if not isinstance(seeds,list) or not seeds or len(seeds)>30 or any(not isinstance(s,str) or not s.strip() for s in seeds):
        raise TraceError("SEEDS", "填写1至30个召回批次")
    return {"seeds":sorted(set(s.strip() for s in seeds))}
