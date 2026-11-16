from fastapi import FastAPI,Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.errors import TraceError
from app.config import ROOT
from app.web import router as web
from app.modules.intake.routes import router as intake
from app.modules.contract.routes import router as contract
from app.modules.genealogy.routes import router as genealogy
from app.modules.recall.routes import router as recall
from app.modules.quarantine.routes import router as quarantine
from app.modules.reconcile.routes import router as reconcile
from app.modules.batches.routes import router as batches
app=FastAPI(title="禾链 · 食品批次追溯",version="1.0.0")
@app.exception_handler(TraceError)
async def trace_error(request:Request,exc:TraceError):
    return JSONResponse({"code":exc.code,"message":exc.message},status_code=exc.status)
@app.get("/health")
def health():return {"status":"ok"}
app.mount("/static",StaticFiles(directory=str(ROOT/"app/static")),name="static")
for router in (intake,contract,genealogy,recall,quarantine,reconcile,batches,web):app.include_router(router)
