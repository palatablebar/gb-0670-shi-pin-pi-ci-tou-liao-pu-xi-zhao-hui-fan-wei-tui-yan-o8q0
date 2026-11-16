from collections import defaultdict
from decimal import Decimal
def balance(edges,input_rows,bad,excluded,blank_lines):
    groups=defaultdict(list);used=defaultdict(lambda:Decimal(0))
    for row in edges:
        groups[row["to_lot"]].append(row);used[row["from_lot"]]+=Decimal(row["kg"])
    accounts=[]
    for lot,rows in sorted(groups.items()):
        intake=sum((Decimal(r["kg"]) for r in rows),Decimal(0))
        output=Decimal(rows[0]["output_kg"]);loss=Decimal(rows[0]["loss_kg"])
        accounts.append({"lot":lot,"input_kg":str(intake),"output_kg":str(output),"loss_kg":str(loss),
                        "remaining_kg":str(output-used[lot]),"difference_kg":str(intake-output-loss),
                        "lines":[r["line"] for r in rows]})
    count_ok=input_rows==len(edges)+len(bad)+len(excluded)
    mass_ok=all(Decimal(a["difference_kg"])==0 and Decimal(a["remaining_kg"])>=0 for a in accounts)
    return {"input_rows":input_rows,"accepted":len(edges),"isolated":len(bad),"excluded":len(excluded),
            "blank_lines":blank_lines,"count_ok":count_ok,"mass_ok":mass_ok,"accounts":accounts,
            "input_kg":str(sum((Decimal(a["input_kg"]) for a in accounts),Decimal(0))),
            "output_kg":str(sum((Decimal(a["output_kg"]) for a in accounts),Decimal(0))),
            "loss_kg":str(sum((Decimal(a["loss_kg"]) for a in accounts),Decimal(0)))}
