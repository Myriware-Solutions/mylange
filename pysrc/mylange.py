# IMPORTS
import os
import sys
from interpreter import MylangeInterpreter
from interface import AnsiColor
from lantypes import LanTypes
from version import VERSION
# Vars
def clear_terminal():
    # Check if the operating system is Windows ('nt')
    if os.name == 'nt':
        _ = os.system('cls')
    # Otherwise, assume it's a Unix-like system
    else:
        _ = os.system('clear')

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
file_name:str
if (len(params) >= 2):
    file_name = params[1]
else: linear = True

if not linear:
    structure:MylangeInterpreter = MylangeInterpreter("Main")
    if "--echoes" in params: structure.enable_echos()
    with open(file_name, "r", encoding='utf-8') as f:
        r = structure.interpret(f.read())
        AnsiColor.println(f"Returned with: {r}", AnsiColor.GREEN)
else:
    AnsiColor.println(f"Welcome to Mylange Linear Interface!\nRunning Mylange verison {VERSION}\nUse CTRL+C or \"return 0\" to close the interpreter.", AnsiColor.CYAN)
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
            chevron = AnsiColor.colorize(">> " if no_more_indent(index_levels) else f".. {("  "*sum(index_levels.values()))}", AnsiColor.BLUE)
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
                        res = mi.interpret(input_str)
                        if (res.typeid == LanTypes.integer) and (res.value == 0):
                            running = False
                input_str = ""
            else:
                input_str += in_str
        except KeyboardInterrupt:
            running = False
        except Exception as e:
            AnsiColor.println(e.with_traceback() if (mi.EchosEnables) else e, AnsiColor.RED)
            errors.append(e)
            input_str = ""
    AnsiColor.println(f"Goodbye! :)", AnsiColor.CYAN)