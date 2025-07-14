# IMPORTS
import sys
from interpreter import MylangeInterpreter
from interface import AnsiColor
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
    with open(file_name, "r") as f:
        r = structure.interpret(f.read())
        AnsiColor.println(f"Returned with: {r}", AnsiColor.GREEN)
else:
    print("Welcome to Mylange Linear Interface!")
    mi = MylangeInterpreter("Linear")
    while True:
        input_str:str = input(AnsiColor.colorize("> ", AnsiColor.MAGENTA))
        if input_str == "exit": break
        mi.interpret(input_str)
    AnsiColor.println(f"Goodbye! :)", AnsiColor.CYAN)