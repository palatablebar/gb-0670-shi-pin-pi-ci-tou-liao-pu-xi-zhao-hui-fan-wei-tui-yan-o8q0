from fastapi import APIRouter, Body
from app.modules.contract.service import apply
from app.errors import TraceError
router=APIRouter(prefix="/api/contract",tags=["contract"])
@router.post("")
def run(payload: dict = Body(...)):
    try:
        rows=payload["rows"]
        return apply(rows)
    except (KeyError,TypeError,AttributeError) as exc:
        raise TraceError("FIELDS", "字段缺失或类型错误，请检查输入") from exc
