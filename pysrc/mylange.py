# IMPORTS
import re, os, sys
from interpreter import MylangeInterpreter
from interface import AnsiColor
from lantypes import LanType, LanScaffold
from lanerrors import LanErrors
from lantypes import VariableValue
from version import GET_VERSION

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

HELP_MENU = """*help: this menu.
*clear: clears the screen.
*echoes: Enable Mylange Echoes (debugging purposes).
*err: Print the full log of a previous error.
return 0: exits the program.
"""

def ERRNO_PROMPT(amount:int) -> str:
    return str("errno "*AnsiColor.BLUE) + f"[{amount}]" + str(":"*AnsiColor.BLUE)


# Entry point for using the CLI
linear:bool=False
params:list[str] = sys.argv
file_path:str|None=None
if (len(params) >= 2):
    file_path = params[1]
else: linear = True

if not linear:
    assert file_path is not None
    structure:MylangeInterpreter = MylangeInterpreter("Main", filePath=file_path)
    if "--echoes" in params: structure.enable_echos()
    with open(file_path, "r", encoding='utf-8') as f:
        code = remove_comments(f.read())
        r = "Error"
        try:
            r = structure.interpret(code)
            assert r is not None
            if r.Type.TypeNum == LanScaffold.nil:
                # Check to see if there is a Main class and method
                if "Main" in structure.Booker._class_registry:
                    main_param_types = LanType(LanScaffold.array, [LanType.string()])
                    if structure.Booker.GetClass("Main").has_method("main", [main_param_types]):
                        main_function = structure.Booker.GetClass("Main").get_method("main", [main_param_types])
                        formated_args = [VariableValue[str](LanType.string(), arg) for arg in params[2:]]
                        r = main_function.execute(structure, [VariableValue[list[VariableValue[str]]](main_param_types, formated_args)])
            print(f"Returned with: {r}"*(AnsiColor.YELLOW if r=="Error" else AnsiColor.GREEN))
        except LanErrors.Break:
            print(f"Program Ended with Error"*AnsiColor.RED)
else:
    print(f"Welcome to Mylange Linear Interface!\nRunning Mylange verison {GET_VERSION()}\nUse CTRL+C or \"return 0\" to close the interpreter."*AnsiColor.CYAN)
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
                        try:
                            err_in = int(input(ERRNO_PROMPT(len(errors))).strip())
                            print(errors[int(err_in)])
                        except ValueError:
                            print("Please use numerical input (0-9)!"*AnsiColor.YELLOW)
                        except IndexError:
                            print("Index is outside the error range!"*AnsiColor.YELLOW)
                    case "*help":
                        print(HELP_MENU)
                    case _:
                        res = mi.interpret(input_str)
                        if res is None:
                            print("This code snippet does not work. Try running '*help'."*AnsiColor.YELLOW)
                        elif (res.Type == LanScaffold.integer) and (res.value == 0):
                            running = False
                input_str = ""
            else:
                input_str += in_str
        except KeyboardInterrupt:
            running = False
        except Exception as e:
            raise e
            print(str(e.with_traceback(None))*AnsiColor.RED)
            errors.append(e)
            input_str = ""
    print(f"Goodbye! :)"*AnsiColor.CYAN)