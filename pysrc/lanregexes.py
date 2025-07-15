# IMPORTS
import re
from enum import StrEnum

class LanRe(StrEnum):
    # Line Recongition
    VariableDecleration = r"^(global|local)? *([a-zA-Z\[\]]+) +(\w+) *=(>+) *(.*) *"
    VariableName = r"^([a-zA-Z]\w*)"
    IndexedVariableName = r"^([a-zA-Z]\w*)\[(\d+)\]"
    SetIndexedVariableName = r"^([a-zA-Z]\w*):(\w+)"
    FunctionOrMethodCall = r"^([\w.]+) *\((.*)\)"
    CachedBlock = r"(0x[a-fA-F0-9]+)"
    CachedChar = r"(1x[a-fA-F0-9]+)"
    CachedString = r"^(2x[a-fA-F0-9]+)"
    ReturnStatement= r"^return *(.*)"
    FunctionStatement = r"def +(\w+) +(\w+) *\((.*)\) *as +(.*)"
    ImportStatement = r"from +(\w+) +import +([\w, ]+)"
    ForStatement = r"for +(\w+) +([a-zA-Z]+) +in +(.+) +do (.+)"
    WhileStatement = r"^while *\((.*)\) *do +(.*)"
    BreakStatement = r"^break"
    # If/Else Statements
    IfStatementGeneral = r"if +\(.*\) +then +.*"
    IfElseStatement = r"if *\((.*)\) *then +(.*?) +else +(.*)"
    IfStatement = r"if *\((.*)\) *then +(.*)"
    # Boolean
    GeneralEqualityStatement = r"^(.*?) *([=<>!]+) *(.*)"
    # Arithmetics
    GeneralArithmetics = r"^(.*?) *([+\-*\/]+) *(.*)"
