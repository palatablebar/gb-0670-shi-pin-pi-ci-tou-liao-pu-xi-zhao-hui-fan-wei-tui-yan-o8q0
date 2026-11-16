from app.modules.contract.coerce import normalize
from app.errors import TraceError
from app.reasons import issue
def apply(rows):
    good=[];bad=[]
    for row in rows:
        try: good.append(normalize(row))
        except TraceError as exc: bad.append(issue(row,exc.code))
    return {"rows":good,"issues":bad}
