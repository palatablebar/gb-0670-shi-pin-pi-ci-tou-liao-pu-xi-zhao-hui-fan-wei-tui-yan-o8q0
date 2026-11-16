from fastapi import APIRouter, Body
from app.modules.genealogy.service import resolve
from app.errors import TraceError
router=APIRouter(prefix="/api/genealogy",tags=["genealogy"])
@router.post("")
def run(payload: dict = Body(...)):
    try:
        rows=payload["rows"]
        return resolve(rows)
    except (KeyError,TypeError,AttributeError) as exc:
        raise TraceError("FIELDS", "字段缺失或类型错误，请检查输入") from exc
