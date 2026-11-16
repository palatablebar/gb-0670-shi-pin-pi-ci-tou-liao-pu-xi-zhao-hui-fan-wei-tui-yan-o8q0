from fastapi import APIRouter, Body
from app.modules.intake.service import inspect
from app.errors import TraceError
router=APIRouter(prefix="/api/intake",tags=["intake"])
@router.post("")
def run(payload: dict = Body(...)):
    try:
        data=str(payload["text"]).encode("utf-8")
        return inspect(data)
    except (KeyError,TypeError,AttributeError) as exc:
        raise TraceError("FIELDS", "字段缺失或类型错误，请检查输入") from exc
