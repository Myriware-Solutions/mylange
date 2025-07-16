# IMPORTS
import re
from enum import StrEnum

Redefinitions = r"#def ([^ \n]*) as ([^ \n]*)"

class LanRe(StrEnum):
    # Variables
    VariableDecleration = r"^(global|local)? *([a-zA-Z\[\]]+) +(\w+) *=(>+) *(.*) *"
    VariableStructure = r"^([a-zA-Z]\w*)([\[\]:\w]+)?"
    # Functions
    FunctionStatement = r"def +(\w+) +(\w+) *\((.*)\) *as +(.*)"
    FunctionOrMethodCall = r"^([\w.]+) *\((.*)\)"
    ReturnStatement= r"^return *(.*)"
    # Caches
    CachedBlock = r"(0x[a-fA-F0-9]+)"
    CachedChar = r"(1x[a-fA-F0-9]+)"
    CachedString = r"^(2x[a-fA-F0-9]+)"
    # Imports
    ImportStatement = r"from +(\w+) +import +([\w, ]+)"
    # Loops
    ForStatement = r"for +(\w+) +([a-zA-Z]+) +in +(.+) +do (.+)"
    WhileStatement = r"^while *\((.*)\) *do +(.*)"
    BreakStatement = r"^break"
    # Classes
    ClassStatement = r"^class +([a-zA-Z]\w*) +has +(.*)"
    ProprotyStatement = r"^prop +([a-zA-Z\[\]]+) +(\w+)(?: *=> *(.*) *)?"
    NewClassObjectStatement = r"new +([a-zA-Z]\w*) *\((.*)\)"
    PropertySetStatement = r"this:(.+) +=> +(.*)"
    # If/Else Statements
    IfStatementGeneral = r"if +\(.*\) +then +.*"
    IfElseStatement = r"if *\((.*)\) *then +(.*?) +else +(.*)"
    IfStatement = r"if *\((.*)\) *then +(.*)"
    # Boolean
    GeneralEqualityStatement = r"^(.*?) *([=<>!]+) *(.*)"
    # Arithmetics
    GeneralArithmetics = r"^(.*?) *([+\-*\/]+) *(.*)"
