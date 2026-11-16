from fastapi import APIRouter, Body
from app.modules.recall.service import simulate
from app.errors import TraceError
router=APIRouter(prefix="/api/recall",tags=["recall"])
@router.post("")
def run(payload: dict = Body(...)):
    try:
        edges=payload["edges"]; seeds=payload["seeds"]
        return simulate(edges,seeds)
    except (KeyError,TypeError,AttributeError) as exc:
        raise TraceError("FIELDS", "字段缺失或类型错误，请检查输入") from exc
