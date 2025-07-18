# IMPORTS
import re
from enum import StrEnum

class ActualRegex(StrEnum):
    # Redefinitions
    Redefinitions = "^#!(.*)"
    # Variables
    VariableDecleration = "^([a-zA-Z]+) +(\w+) *=(>+) *(.*) *"
    VariableStructure = "^(\w*)([\[\]:\w]+)?"
    # Functions
    FunctionStatement = "def +(\w+) +(\w+) *\((.*)\) *as +(.*)"
    FunctionOrMethodCall = "^([\w.]+) *\((.*)\)"
    ReturnStatement= "^return *(.*)"
    # Caches
    CachedBlock = "(0x[a-fA-F0-9]+)"
    CachedChar = "(1x[a-fA-F0-9]+)"
    CachedString = "^(2x[a-fA-F0-9]+)"
    # Imports
    ImportStatement = "from +(\w+) +import +([\w, ]+)"
    # Loops
    ForStatement = "for +(\w+) +([a-zA-Z]+) +in +(.+) +do (.+)"
    WhileStatement = "^while *\((.*)\) *do +(.*)"
    BreakStatement = "^break"
    # Classes
    ClassStatement = "^class +([a-zA-Z]\w*) +has +(.*)"
    ProprotyStatement = "^prop +([a-zA-Z\[\]]+) +(\w+)(?: *=> *(.*) *)?"
    NewClassObjectStatement = "new +([a-zA-Z]\w*) *\((.*)\)"
    PropertySetStatement = "this:(.+) +=> +(.*)"
    # If/Else Statements
    IfStatementGeneral = "if +\(.*\) +then +.*"
    IfElseStatement = "if *\((.*)\) *then +(.*?) +else +(.*)"
    IfStatement = "if *\((.*)\) *then +(.*)"
    # Boolean
    GeneralEqualityStatement = "^(.*?) *([=<>!]+) *(.*)"
    # Arithmetics
    GeneralArithmetics = "^(.*?) *([+\-*\/]+) *(.*)"

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