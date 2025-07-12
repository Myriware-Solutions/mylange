# IMPORTS
import sys
import json
from main import MylangeInterpreter, CodeCleaner
# DEF

# Entry point for using the CLI
params:list[str] = sys.argv
file_name:str
if (len(params) >= 2):
    file_name = params[1]
else:
    file_name = input("file> ")
    if (file_name == ""):
        file_name = "debug.my"

structure:MylangeInterpreter = MylangeInterpreter()
with open(file_name, "r") as f:
    structure.interpret(f.read())
    # clean_code, cache = CodeCleaner.cleanup_chunk(f.read())
    # print(json.dumps(cache, indent=2))
    # print(clean_code)
