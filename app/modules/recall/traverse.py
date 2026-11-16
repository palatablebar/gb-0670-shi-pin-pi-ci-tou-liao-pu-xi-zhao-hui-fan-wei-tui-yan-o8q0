from collections import defaultdict,deque
from app.errors import TraceError
def trace(edges, seeds):
    if not seeds or len(seeds)>30 or any(not isinstance(s,str) or not s.strip() for s in seeds):
        raise TraceError("SEEDS", "填写1至30个召回批次")
    adjacency=defaultdict(list); nodes=set()
    for row in edges:
        adjacency[row["from_lot"]].append(row);nodes.update([row["from_lot"],row["to_lot"]])
    missing=sorted(set(seeds)-nodes)
    queue=deque((seed,[seed],[]) for seed in sorted(set(seeds)) if seed in nodes)
    results={}
    while queue:
        lot,path,lines=queue.popleft()
        if lot in results:continue
        results[lot]={"lot":lot,"path":path,"lines":lines,"depth":len(path)-1,"source":path[0]}
        for edge in sorted(adjacency.get(lot,[]),key=lambda r:(r["to_lot"],r["line"])):
            queue.append((edge["to_lot"],path+[edge["to_lot"]],lines+[edge["line"]]))
    return {"lots":list(results.values()),"unknown_seeds":missing,"count":len(results),"seeds":sorted(set(seeds))}
