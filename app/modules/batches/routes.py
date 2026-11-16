import base64, binascii
from fastapi import APIRouter, Body
from fastapi.responses import Response
from app import store
from app.config import SAMPLE_DIR
from app.errors import TraceError
from app.modules.batches.service import execute
from app.modules.batches.archive import evidence
router=APIRouter(prefix="/api",tags=["batches"])
def source(payload):
    if "source_b64" in payload:
        try:return base64.b64decode(payload["source_b64"],validate=True)
        except (ValueError,TypeError,binascii.Error) as exc:raise TraceError("BASE64","文件内容无效，请重新选择") from exc
    if "text" in payload:
        if not isinstance(payload["text"],str):raise TraceError("TEXT","台账必须为文本")
        return payload["text"].encode("utf-8")
    name=payload.get("sample","dirty")
    if name not in {"clean","dirty","legacy"}:raise TraceError("SAMPLE","样例不存在",404)
    return (SAMPLE_DIR/(name+".csv")).read_bytes()
@router.post("/runs")
def run(payload:dict=Body(default={})):
    return execute(source(payload),payload.get("seeds",["R-0001"]))
@router.get("/batches")
def batches():return store.history()
@router.get("/runs/{key}")
def get(key:str):return store.get(key)
@router.post("/runs/{key}/review")
def review(key:str,payload:dict=Body(...)):
    version=payload.get("version")
    if type(version) is not int:raise TraceError("VERSION","复核版本必须为整数")
    note=payload.get("note","")
    if not isinstance(note,str) or len(note)>500:raise TraceError("NOTE","复核依据最长500字")
    return store.review(key,version,payload.get("state"),note)
@router.get("/runs/{key}/evidence.csv")
def export(key:str):
    return Response(evidence(store.get(key)),media_type="text/csv",headers={"Content-Disposition":"attachment; filename=evidence.csv"})

@router.post("/runs/{key}/rerun")
def rerun(key:str):
    old=store.get(key)
    return execute(base64.b64decode(old["source_b64"]),old["manifest"]["parameters"]["seeds"])
