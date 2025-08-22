from lanregexes import ActualRegex

while True:
    i = input("> ")
    match i:
        case t if ActualRegex.ReturnStatement.value.match(i):
            print(t)