from app.modules.intake.reader import read
def inspect(data):
    result=read(data)
    result["preview"]=result["rows"][:80]
    return result
