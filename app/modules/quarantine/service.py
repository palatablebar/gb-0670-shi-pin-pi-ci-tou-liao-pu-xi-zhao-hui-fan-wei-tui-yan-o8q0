from app.modules.quarantine.checks import inspect,distribution
def validate(edges):
    result=inspect(edges)
    result["distribution"]=distribution(result["issues"])
    return result
