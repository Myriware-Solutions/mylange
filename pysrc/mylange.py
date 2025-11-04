# IMPORTS
import re, os, sys
from interpreter import MylangeInterpreter
from interface import AnsiColor
from lantypes import LanType, LanScaffold
from importlib.metadata import version
# Vars

def remove_comments(string:str) -> str:
        result:str = re.sub(r"^//.*$", '', string, flags=re.MULTILINE)
        result = re.sub(r"/\[[\w\W]*\]/", '', result, flags=re.MULTILINE)
        return result
def clear_terminal():
    # Check if the operating system is Windows ('nt')
    if os.name == 'nt': _ = os.system('cls')
    # Otherwise, assume it's a Unix-like system
    else: _ = os.system('clear')

def get_levels(string:str) -> dict[str, int]:
    Return = {}
    Return["sq"] = string.count("{") - string.count("}")
    Return["br"] = string.count("[") - string.count("]")
    Return["pa"] = string.count("(") - string.count(")")
    return Return

def no_more_indent(levels:dict[str, int]) -> bool:
    for val in levels.values():
        if val != 0: return False
    return True

# Entry point for using the CLI
linear:bool=False
params:list[str] = sys.argv
file_name:str|None=None
if (len(params) >= 2):
    file_name = params[1]
else: linear = True

if not linear:
    structure:MylangeInterpreter = MylangeInterpreter("Main")
    if "--echoes" in params: structure.enable_echos()
    assert file_name is not None
    with open(file_name, "r", encoding='utf-8') as f:
        code = remove_comments(f.read())
        r = structure.interpret(code)
        if r is None:
            print(f"Program Ended with Error"*AnsiColor.RED)
        else: 
            print(f"Returned with: {r}"*AnsiColor.GREEN)
else:
    print(f"Welcome to Mylange Linear Interface!\nRunning Mylange verison {version("mylange")}\nUse CTRL+C or \"return 0\" to close the interpreter."*AnsiColor.CYAN)
    mi = MylangeInterpreter("Linear")
    running:bool = True
    input_str:str = ""
    index_levels:dict[str, int] = {
        "sq": 0,
        "br": 0,
        "pa": 0
    }
    errors:list[Exception] = []
    while running:
        try:
            chevron = (">> " if no_more_indent(index_levels) else f".. {("  "*sum(index_levels.values()))}")*AnsiColor.BLUE
            in_str:str = input(chevron)
            for key, val in get_levels(in_str).items():
                index_levels[key] += val
            if (no_more_indent(index_levels)):
                input_str += in_str
                match (input_str):
                    case "exit":
                        print("Trying to exit? Run 'return 0'")
                    case "*clear":
                        clear_terminal()
                    case "*echoes":
                        mi.enable_echos()
                    case "*err":
                        err_in = input(f"errno [{len(errors)}]: ")
                        print(errors[int(err_in)])
                    case _:
                        res = mi.interpret(input_str); assert res is not None
                        if (res.Type == LanScaffold.integer) and (res.value == 0):
                            running = False
                input_str = ""
            else:
                input_str += in_str
        except KeyboardInterrupt:
            running = False
        except Exception as e:
            print(str(e.with_traceback(None))*AnsiColor.RED)
            errors.append(e)
            input_str = ""
    print(f"Goodbye! :)"*AnsiColor.CYAN)