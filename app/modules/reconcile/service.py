from app.modules.reconcile.balance import balance
def compare(edges,intake,issues,excluded):
    return balance(edges,intake["input_rows"],issues,excluded,intake["blank_lines"])
