from collections import defaultdict, deque
from app.reasons import issue
def reachable(adjacency, start, target):
    queue=deque([start]);seen=set()
    while queue:
        node=queue.popleft()
        if node==target:return True
        if node in seen:continue
        seen.add(node);queue.extend(adjacency.get(node,[]))
    return False
def signature(row):
    return tuple(row[k] for k in ("from_lot","to_lot","kg","output_kg","loss_kg","status"))
def build(rows):
    groups=defaultdict(list)
    for row in rows:groups[row["event_id"]].append(row)
    candidates=[];excluded=[];bad=[]
    for event,versions in sorted(groups.items()):
        highest=max(r["revision"] for r in versions)
        top=[r for r in versions if r["revision"]==highest]
        for row in versions:
            if row["revision"]!=highest:excluded.append(issue(row,"SUPERSEDED"))
        if len({signature(r) for r in top})>1:
            bad.extend(issue(r,"CONFLICT") for r in top);continue
        winner=min(top,key=lambda r:r["line"])
        excluded.extend(issue(r,"DUPLICATE") for r in top if r is not winner)
        if winner["status"]=="void":excluded.append(issue(winner,"VOID"));continue
        candidates.append(winner)
    adjacency=defaultdict(list);edges=[]
    for row in sorted(candidates,key=lambda r:(r["from_lot"],r["to_lot"],r["event_id"])):
        if reachable(adjacency,row["to_lot"],row["from_lot"]):
            bad.append(issue(row,"CYCLE"));continue
        adjacency[row["from_lot"]].append(row["to_lot"]);edges.append(row)
    return {"edges":edges,"issues":bad,"excluded":excluded,"adjacency":dict(adjacency)}
