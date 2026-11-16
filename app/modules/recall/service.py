from app.modules.recall.traverse import trace
def simulate(edges,seeds):
    result=trace(edges,seeds)
    children={r["from_lot"] for r in edges}
    result["terminal_lots"]=[r["lot"] for r in result["lots"] if r["lot"] not in children]
    return result
