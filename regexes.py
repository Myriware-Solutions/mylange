# IMPORTS
import re
from enum import StrEnum

class LanRe(StrEnum):
    # Line Recongition
    VariableDecleration = r"^(global|local)? *([a-zA-Z\[\]]+) +(\w+) *=(>+) *(.*) *"
    FunctionOrMethodCall = r"^([\w.]+) *\((.*)\)"
    CachedBlock = r"(0x[a-fA-F0-9]+)"
    CachedChar = r"(1x[a-fA-F0-9]+)"
    CachedString = r"(2x[a-fA-F0-9]+)"
    # If/Else Statements
    IfStatementGeneral = r"if +\(.*\) +then +.*"
    IfElseStatement = r"if *\((.*)\) *then +(.*?) +else +(.*)"
    IfStatement = r"if *\((.*)\) *then +(.*)"
