# IMPORTS
import sys
from interpreter import MylangeInterpreter
# Entry point for using the CLI
linear:bool=False
params:list[str] = sys.argv
file_name:str
if (len(params) >= 2):
    file_name = params[1]
else: linear = True

if not linear:
    structure:MylangeInterpreter = MylangeInterpreter("Main")
    with open(file_name, "r") as f:
        r = structure.interpret(f.read())
        print(f"\033[32mReturned with: {r}\033[0m")
else:
    print("Welcome to Mylange Linear Interface!")
    mi = MylangeInterpreter("Linear")
    while True:
        input_str:str = input("> ")
        if input_str == "exit": break
        mi.interpret(input_str)
    print("Goodbye! :)")