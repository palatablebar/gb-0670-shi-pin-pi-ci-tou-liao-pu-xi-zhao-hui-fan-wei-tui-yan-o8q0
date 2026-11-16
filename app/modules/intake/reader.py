import csv, io
from app.config import COLUMNS, MAX_BYTES, MAX_ROWS
from app.errors import TraceError
from app.reasons import issue
def decode(data):
    if len(data) > MAX_BYTES:
        raise TraceError("TOO_LARGE", "文件超过2MB，请分批导入", 413)
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            pass
    raise TraceError("ENCODING", "编码无法识别，请另存为UTF-8")
def read(data):
    text, encoding=decode(data)
    if not text:
        raise TraceError("EMPTY_FILE", "文件为空，请选择台账")
    reader=csv.reader(io.StringIO(text,newline=""), strict=True)
    rows=[]; bad=[]; blanks=0; headers=0
    try:
        header=next(reader,None)
        if not header:
            raise TraceError("BLANK_FILE", "文件只有空行，请补充台账")
        if header != COLUMNS:
            raise TraceError("HEADER", "字段不匹配，请使用样例表头")
        previous=reader.line_num
        for cells in reader:
            line=previous+1;previous=reader.line_num
            if not cells or all(not c.strip() for c in cells):
                blanks+=1;continue
            if cells == COLUMNS:
                headers+=1;continue
            if len(rows)+len(bad) >= MAX_ROWS:
                raise TraceError("TOO_MANY_ROWS", "行数超过15000，请拆分文件", 413)
            if len(cells)!=len(COLUMNS):
                bad.append(issue({"line":line,"raw":cells},"COLUMN_COUNT"));continue
            row=dict(zip(COLUMNS,cells)); rows.append({"line":line,"raw":row})
    except csv.Error as exc:
        raise TraceError("CSV_BROKEN", "引号未闭合，请修复后重试") from exc
    if not rows and not bad:
        raise TraceError("BLANK_ROWS" if blanks else "HEADER_ONLY", "没有业务记录，请补充投料台账")
    return {"rows":rows,"issues":bad,"blank_lines":blanks,"repeated_headers":headers,"encoding":encoding,"input_rows":len(rows)+len(bad)}
