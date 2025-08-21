# IMPORTS
import os
import sys
from interpreter import MylangeInterpreter
from interface import AnsiColor
# Vars
version:str = "0.0.1"
def clear_terminal():
    # Check if the operating system is Windows ('nt')
    if os.name == 'nt':
        _ = os.system('cls')
    # Otherwise, assume it's a Unix-like system
    else:
        _ = os.system('clear')


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
    AnsiColor.println(f"Welcome to Mylange Linear Interface!\nRunning Mylange verison {version}\nUse CTRL+C or *exit to close the interpreter.", AnsiColor.CYAN)
    mi = MylangeInterpreter("Linear")
    running:bool = True
    while running:
        try:
            input_str:str = input(AnsiColor.colorize("> ", AnsiColor.MAGENTA))
            match (input_str):
                case "exit":
                    print("Trying to exit? Run '*exit'")
                case "*exit":
                    running = False
                case "*clear":
                    clear_terminal()
                case "*echoes":
                    mi.enable_echos()
                case _:
                    v = None
                    try:
                        v = mi.format_parameter(input_str)
                    except: pass
                    if (v != None):
                        print(v)
                    else:
                        mi.interpret(input_str)
        except KeyboardInterrupt:
            running = False
        except Exception as e:
            AnsiColor.println(e.with_traceback(), AnsiColor.RED)
    AnsiColor.println(f"Goodbye! :)", AnsiColor.CYAN)