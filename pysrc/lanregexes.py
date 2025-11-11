# IMPORTS
import re
from enum import StrEnum, Enum, unique

VariableStructureRaw = r"^(\w*)([\[\]:\w]+)?"

@unique
class ActualRegex(Enum):
    # Redefinitions
    Redefinitions = re.compile(r"^#!(.*)", flags=re.UNICODE)
    # Variables
    VariableStructure = re.compile(VariableStructureRaw, flags=re.UNICODE)
    #VariableDecleration = re.compile(r"^(.*) *([a-zA-Z]+) +(\w+) *=(>+) *(.*) *", flags=re.UNICODE)
    VariableDecleration = re.compile(r"^\s*([a-zA-Z<>,|\s]+) +(\w+) *=(>+) *(.*) *", flags=re.UNICODE)
    VariableRedeclaration = re.compile(r"^(\w*)([\[\]:\w]+)? *=> *(.*) *$", flags=re.UNICODE)
    # Functions
    FunctionStatement = re.compile(r"def +(\w+) +(\w+) *\((.*)\) *as +(.*)", flags=re.UNICODE)
    FunctionOrMethodCall = re.compile(VariableStructureRaw.replace(r"(\w*)", r"([\w.]*)").replace(r":", r":.") + r" *\((.*)\) *$", flags=re.UNICODE)
    ReturnStatement= re.compile(r"^return *(.*)", flags=re.UNICODE)
    LambdaStatement = re.compile(r"(\w+) *\(([\w ,]+)\) *as *(\w+)", flags=re.UNICODE)
    LambdaStatementFull = re.compile(r"(\w+) *\(([\w ,]+)\) *=> *{(\w+)}", flags=re.UNICODE)
    # Caches
    CachedBlock = re.compile(r"(0x[a-fA-F0-9]+)", flags=re.UNICODE)
    CachedChar = re.compile(r"(1x[a-fA-F0-9]+)", flags=re.UNICODE)
    CachedString = re.compile(r"^(2x[a-fA-F0-9]+)", flags=re.UNICODE)
    # Imports
    ImportStatement = re.compile(r"from +(.+?) +import +([\w, ]+)", flags=re.UNICODE)
    # Loops
    ForStatement = re.compile(r"^for +((?:\w+ +[a-zA-Z]+)|(?:\[[a-zA-Z ,]+\])) +in +(.+) +do (.+)", flags=re.UNICODE)
    WhileStatement = re.compile(r"^while *\((.*)\) *do +(.*)", flags=re.UNICODE)
    BreakStatement = re.compile(r"^break", flags=re.UNICODE)
    # Classes
    ClassStatement = re.compile(r"^class +([a-zA-Z]\w*) +has +(.*)", flags=re.UNICODE)
    PropertyStatement = re.compile(r"^(public|private)\s*(?!def)([\w]+)\s+(\w+)(?:\s*=>\s*(.*)\s*)?", flags=re.UNICODE)
    NewClassObjectStatement = re.compile(r"new +([a-zA-Z]\w*) *\((.*)\)", flags=re.UNICODE)
    ClassMethodStatement = re.compile(r"(\w+)\s*def\s*(\w+)\s*(\w+|:|\[\s*\])\s*\(([\w\s,.]*)\)\s*as\s*(.*)", flags=re.UNICODE)
    # If/Else Statements
    IfStatementBlock = re.compile(r"(?:(?:if\s*.*)|(?:else\s+if\s*.*)|(?:else\s*.*))+", flags=re.UNICODE)
    IfStatementParts = re.compile(r"(if|else\s*if|else)\s*(?:\((.*?)\))?\s*then\s*(.*?)(?=if|else\s*if|else|$)", flags=re.UNICODE)
    # Boolean
    GeneralEqualityStatement = re.compile(r"^(.*?) *([=<>!]+) *(.*) *$", flags=re.UNICODE)
    # Arithmetics
    GeneralArithmetics = re.compile(r"^(.*?) *([.+\-*\/]+) *(.*) *$", flags=re.UNICODE)
    # Set 
    SetInners = re.compile(r"\((?:\s*\w+\s*=>\s*.+,?)+\)", flags=re.UNICODE)

