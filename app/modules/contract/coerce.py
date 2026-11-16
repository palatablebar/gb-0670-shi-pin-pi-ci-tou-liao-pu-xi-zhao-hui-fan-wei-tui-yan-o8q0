from decimal import Decimal, InvalidOperation
import unicodedata
from app.config import NULLS, UNITS
from app.errors import TraceError
def number(value):
    text=unicodedata.normalize("NFKC",str(value)).strip()
    if text.upper() in NULLS:
        raise TraceError("NULL_VALUE", "必要数量为空")
    try:
        result=Decimal(text.replace(",", ""))
        if not result.is_finite():
            raise InvalidOperation
        if result.adjusted()>12 or result.as_tuple().exponent < -6 or result.copy_abs()>Decimal("1e12"):
            raise TraceError("BAD_DECIMAL", "数量超出范围或超过6位小数")
        return result
    except InvalidOperation as exc:
        raise TraceError("BAD_DECIMAL", "数量无法解析") from exc
def normalize(record):
    raw=record["raw"]
    for key in ("event_id","from_lot","to_lot"):
        if raw[key].strip().upper() in NULLS:
            raise TraceError("NULL_VALUE", "必要编号为空")
    unit=raw["unit"].strip()
    if unit not in UNITS:
        raise TraceError("BAD_UNIT", "计量单位未知")
    quantity=number(raw["quantity"])*Decimal(UNITS[unit])
    output,loss=number(raw["output_kg"]),number(raw["loss_kg"])
    if quantity<=0 or output<0 or loss<0:
        raise TraceError("NEGATIVE", "投料须大于零，产损不可为负")
    if raw["status"].strip() not in {"active","void"}:
        raise TraceError("BAD_STATE", "事件状态无效")
    revision=raw["revision"].strip()
    if not revision.isascii() or not revision.isdigit() or int(revision)<1:
        raise TraceError("BAD_REVISION", "事件版本必须为正整数")
    return {**record, **{k:raw[k].strip() for k in ("event_id","from_lot","to_lot","note")},
            "kg":str(quantity),"output_kg":str(output),"loss_kg":str(loss),
            "status":raw["status"].strip(),"revision":int(revision)}
