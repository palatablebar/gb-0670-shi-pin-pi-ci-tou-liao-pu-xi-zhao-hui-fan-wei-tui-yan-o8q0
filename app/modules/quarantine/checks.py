from collections import defaultdict, Counter
from decimal import Decimal
from app.reasons import issue
def inspect(edges):
    current=list(edges);bad=[]
    while True:
        groups=defaultdict(list)
        for r in current:groups[r["to_lot"]].append(r)
        reasons={}
        produced={}
        for child,rows in groups.items():
            definitions={(r["output_kg"],r["loss_kg"]) for r in rows}
            if len(definitions)>1:
                for r in rows:reasons[r["line"]]="SPEC_CONFLICT"
                continue
            output,loss=map(Decimal,next(iter(definitions)))
            produced[child]=output
            if sum((Decimal(r["kg"]) for r in rows),Decimal(0))!=output+loss:
                for r in rows:reasons[r["line"]]="MASS_GAP"
        outgoing=defaultdict(list)
        for r in current:outgoing[r["from_lot"]].append(r)
        for parent,rows in outgoing.items():
            if not parent.startswith("R-") and parent not in produced:
                for r in rows:reasons[r["line"]]="ORPHAN"
            elif parent in produced and sum((Decimal(r["kg"]) for r in rows),Decimal(0))>produced[parent]:
                for r in rows:reasons[r["line"]]="OVERDRAW"
        if not reasons:break
        rejected={r["to_lot"] for r in current if r["line"] in reasons}
        # A child loses its complete recipe when one input is rejected.
        for r in current:
            if r["to_lot"] in rejected and r["line"] not in reasons:reasons[r["line"]]="MASS_GAP"
        remaining=[]
        for r in current:
            if r["line"] in reasons:bad.append(issue(r,reasons[r["line"]]))
            else:remaining.append(r)
        current=remaining
    return {"edges":current,"issues":bad}
def distribution(issues):
    return [{"reason":k,"count":v} for k,v in sorted(Counter(r["reason"] for r in issues).items())]
