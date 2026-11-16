from fastapi import APIRouter, Body
from app.modules.quarantine.service import validate
from app.errors import TraceError
router=APIRouter(prefix="/api/quarantine",tags=["quarantine"])
@router.post("")
def run(payload: dict = Body(...)):
    try:
        edges=payload["edges"]
        return validate(edges)
    except (KeyError,TypeError,AttributeError) as exc:
        raise TraceError("FIELDS", "字段缺失或类型错误，请检查输入") from exc
