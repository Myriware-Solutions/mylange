# IMPORTS
import sys
from interpreter import MylangeInterpreter
# Entry point for using the CLI
linear:bool=False
params:list[str] = sys.argv
file_name:str
if (len(params) >= 2):
    if params[1] == "--linear": linear = True
    else: file_name = params[1]
else:
    file_name = input("file> ")
    if (file_name == ""):
        file_name = "debug.my"
    elif (file_name == "--linear"): linear = True

if not linear:
    structure:MylangeInterpreter = MylangeInterpreter("Main")
    with open(file_name, "r") as f:
        structure.interpret(f.read())
else:
    print("Welcome to Mylange Linear Interface!")
    mi = MylangeInterpreter("Linear")
    while True:
        input_str:str = input("> ")
        if input_str == "exit": break
        mi.interpret(input_str)
    print("Goodbye! :)")