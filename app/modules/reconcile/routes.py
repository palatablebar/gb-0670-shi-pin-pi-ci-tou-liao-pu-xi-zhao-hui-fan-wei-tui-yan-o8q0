from fastapi import APIRouter, Body
from app.modules.reconcile.service import compare
from app.errors import TraceError
router=APIRouter(prefix="/api/reconcile",tags=["reconcile"])
@router.post("")
def run(payload: dict = Body(...)):
    try:
        edges=payload["edges"]; intake=payload["intake"]; issues=payload["issues"]; excluded=payload["excluded"]
        return compare(edges,intake,issues,excluded)
    except (KeyError,TypeError,AttributeError) as exc:
        raise TraceError("FIELDS", "字段缺失或类型错误，请检查输入") from exc
