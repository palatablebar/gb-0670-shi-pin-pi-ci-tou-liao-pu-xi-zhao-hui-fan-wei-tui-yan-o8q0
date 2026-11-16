import base64, binascii
from fastapi import APIRouter, Body
from fastapi.responses import Response
from app import store
from app.errors import TraceError
from app.modules.amendment.service import execute
from app.modules.amendment.archive import export
router = APIRouter(prefix="/api/amendments", tags=["amendments"])
def _bytes(payload):
    if "source_b64" in payload:
        try:
            return base64.b64decode(payload["source_b64"], validate=True)
        except (ValueError, TypeError, binascii.Error) as exc:
            raise TraceError("BASE64", "修订文件内容无效，请重新选择") from exc
    if "text" in payload:
        if not isinstance(payload["text"], str):
            raise TraceError("TEXT", "修订台账必须为文本")
        return payload["text"].encode("utf-8")
    raise TraceError("AMEND_SOURCE", "请提供修订台账 text 或 source_b64", 422)
@router.post("/{baseline_id}")
def amend(baseline_id: str, payload: dict = Body(...)):
    data = _bytes(payload)
    seeds = payload.get("seeds", ["R-0001"])
    return execute(baseline_id, data, seeds, payload.get("mode", "pending"))
@router.get("")
def history():
    return store.amendment_history()
@router.get("/{amendment_id}")
def get(amendment_id: str):
    return store.get_amendment(amendment_id)
@router.get("/{amendment_id}/evidence.csv")
def evidence(amendment_id: str):
    payload = store.get_amendment(amendment_id)
    return Response(export(payload), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=amendment_evidence.csv"})
