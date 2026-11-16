import time, base64
from app.manifest import identity
from app import store
from app.modules.intake.service import inspect
from app.modules.contract.service import apply
from app.modules.genealogy.service import resolve
from app.modules.quarantine.service import validate
from app.modules.recall.service import simulate
from app.modules.reconcile.service import compare
from app.modules.batches.archive import parameters
def execute(data,seeds):
    started=time.perf_counter();params=parameters(seeds);manifest=identity(data,params)
    try:return store.get(manifest["run_id"])
    except Exception as exc:
        from app.errors import TraceError
        if not isinstance(exc,TraceError) or exc.status!=404:raise
    intake=inspect(data);contract=apply(intake["rows"]);graph=resolve(contract["rows"]);quality=validate(graph["edges"])
    issues=intake["issues"]+contract["issues"]+graph["issues"]+quality["issues"]
    reconciliation=compare(quality["edges"],intake,issues,graph["excluded"])
    manifest["elapsed_ms"]=round((time.perf_counter()-started)*1000,2)
    payload={"source_b64":base64.b64encode(data).decode("ascii"),"manifest":manifest,"intake":intake,"contract":contract,"edges":quality["edges"],"quarantine":issues,
             "excluded":graph["excluded"],"recall":simulate(quality["edges"],params["seeds"]),"reconcile":reconciliation}
    return store.save(payload)
