# IMPORTS
import re
from enum import StrEnum

class ActualRegex(StrEnum):
    # Redefinitions
    Redefinitions = r"^#!(.*)"
    # Variables
    VariableDecleration = r"^(.*) *([a-zA-Z]+) +(\w+) *=(>+) *(.*) *"
    VariableStructure = r"^(\w*)([\[\]:\w]+)?"
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

class LanReClass:
    ImportStatement:str
    VariableDecleration:str; VariableStructure:str
    FunctionStatement:str; FunctionOrMethodCall:str; ReturnStatement:str
    CachedBlock:str; CachedChar:str; CachedString:str
    ForStatement:str; WhileStatement:str; BreakStatement:str
    ClassStatement:str; ProprotyStatement:str; NewClassObjectStatement:str; PropertySetStatement:str
    IfStatementGeneral:str; IfElseStatement:str; IfStatement:str
    GeneralEqualityStatement:str; GeneralArithmetics:str

    Translations:dict[str,str] = { }

    def __getattribute__(this, name:str) -> str:
        match (name):
            case "add_translation":
                return super().__getattribute__("add_translation")
            case "search":
                return super().__getattribute__("search")
            case "match":
                return super().__getattribute__("match")
            case "Translations":
                return super().__getattribute__("Translations")
            case _:
                baseString:str = ActualRegex[name]
                for key, value in this.Translations.items():
                    baseString = baseString.replace(key, value)
                return baseString
    def add_translation(this, key:str, value:str) -> None:
        if key in this.Translations.keys():
            raise Exception("Cannot override translations.")
        this.Translations[key] = value

    def search(_, regex:str, string:str) -> re.Match[str] | None:
        return re.search(regex, string, flags=re.UNICODE)
    
    def match(_, regex:str, string:str) -> re.Match[str] | None:
        return re.search(regex, string, flags=re.UNICODE)

LanRe = LanReClass()