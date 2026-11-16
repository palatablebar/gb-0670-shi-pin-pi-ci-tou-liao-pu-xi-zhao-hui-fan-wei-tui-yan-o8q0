REASONS = {
 "COLUMN_COUNT": "列数不齐", "BAD_DECIMAL": "数量无法解析", "NULL_VALUE": "必要字段为空",
 "BAD_UNIT": "计量单位未知", "BAD_STATE": "事件状态无效", "BAD_REVISION": "版本无效",
 "NEGATIVE": "数量不能为负", "CONFLICT": "同版本事件冲突", "DUPLICATE": "相同事件重复",
 "SUPERSEDED": "旧版本已替代", "CYCLE": "投料形成环", "MASS_GAP": "投入与产损不等",
 "SPEC_CONFLICT": "同批产损定义冲突", "OVERDRAW": "领用超过产出", "ORPHAN": "来源批次失联",
 "VOID": "事件已撤回", "OK": "通过"}
def issue(row, code):
    return {"line": row.get("line", 0), "reason": code, "message": REASONS.get(code, code), "raw": row.get("raw", row)}
