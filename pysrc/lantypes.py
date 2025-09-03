# IMPORTS
from enum import IntEnum, Enum
from lanregexes import ActualRegex
import re

# Type castisting for variables

class VariableValue:
    typeid:int
    def __init__(this, typeid:int, value:any=None):
        from lanclass import LanClass
        this.typeid = typeid
        this.value:None|bool|int|str|list['VariableValue']|dict[str,'VariableValue']|LanClass = None
        if (value != None): this.value = value

    def __str__(this):
        match (this.typeid):
            case LanTypes.nil:
                return 'nil'
            case LanTypes.boolean:
                return f"{this.value}".lower()
            case LanTypes.integer:
                return f"{this.value}"
            case LanTypes.character:
                return f"'{this.value}'"
            case LanTypes.string:
                return f'"{this.value}"'
            case LanTypes.array:
                larray = [f"{item}" for item in this.value]
                return f"[{', '.join(larray)}]"
            case LanTypes.set:
                lset = [f"{k}:{v}" for k, v in this.value.items()]
                return f"({', '.join(lset)})"
        return f"<{this.value}@{this.typeid}>"
    
    def isof(this, type:int) -> bool:
        return this.typeid == type
    
    def to_string(this):
        match (this.typeid):
            case LanTypes.boolean:
                return f"{this.value}".lower()
            case LanTypes.integer:
                return f"{this.value}"
            case LanTypes.character | LanTypes.string:
                return this.value
            case _:
                return this.__str__()
            
    def colon_access(this, index:str) -> 'VariableValue':
        from builtinfunctions import ParamChecker
        ParamChecker.EnsureIntegrety((this, LanTypes.set))
        return this.value[index]

    def bracket_access(this, index:int) -> 'VariableValue':
        from builtinfunctions import ParamChecker
        ParamChecker.EnsureIntegrety((this, LanTypes.array))
        return this.value[index]

class RandomTypeConversions:
    @staticmethod
    def convert(string:str, mylangeInterpreter=None) -> VariableValue:
        typeid, other = RandomTypeConversions.get_type(string)
        match (typeid):
            case LanTypes.nil:
                return VariableValue(LanTypes.nil, None)
            case LanTypes.boolean if other == 0:
                return VariableValue(LanTypes.boolean, False)
            case LanTypes.boolean if other == 1:
                return VariableValue(LanTypes.boolean, True)
            case LanTypes.integer:
                return VariableValue(LanTypes.integer, int(string))
            case LanTypes.character:
                return VariableValue(LanTypes.character, string[1:-1])
            case LanTypes.string:
                return VariableValue(LanTypes.string, string[1:-1])
            case LanTypes.array:
                insides:str = string[1:-1]
                from interpreter import MylangeInterpreter, CodeCleaner
                mi:MylangeInterpreter = mylangeInterpreter
                parts:list[str] = [item.strip() for item in CodeCleaner.split_top_level_commas(insides)]
                ReturnL:list = []
                for item in parts:
                    var = mi.format_parameter(item)
                    ReturnL.append(var)
                return VariableValue(LanTypes.array, ReturnL)
            case LanTypes.set:
                insides:str = string[1:-1]
                from interpreter import MylangeInterpreter, CodeCleaner
                mi:MylangeInterpreter = mylangeInterpreter
                parts:list[str] = [item.strip() for item in CodeCleaner.split_top_level_commas(insides)]
                ReturnS:dict = {}
                for part in parts:
                    key_value = part.split('=>', 1)
                    var = mi.format_parameter(key_value[1])
                    ReturnS[key_value[0].strip()] = var
                return VariableValue(LanTypes.set, ReturnS)

    @staticmethod
    def get_type(string:str) -> tuple[int, int]:
        # nil
        if (string == 'nil'):
            return (LanTypes.nil, 0)
        # Boolean 
        if (string == "true"):
            return (LanTypes.boolean, 1)
        elif (string == "false"):
            return (LanTypes.boolean, 0)
        # Int 
        try:
            _ = int(string)
            return (LanTypes.integer, 0)
        except: pass
        # Character
        if (string.startswith("'")) and (string.endswith("'")):
            print("char")
            return (LanTypes.character, 0)
        # String 
        if (string.startswith('"')) and (string.endswith('"')):
            return (LanTypes.string, 0)
        # Array 
        if (string.startswith('[')) and (string.endswith(']')):
            return (LanTypes.array, 0)
        # Set
        if (string.startswith('(')) and (string.endswith(')')):
            if re.search(ActualRegex.SetInners.value, string) or re.search(r"\(\s*\)", string):
                return (LanTypes.set, 0)
            else: return (LanTypes.nil, 0)
        # No value found, returning Nil
        return (LanTypes.nil, 0)

class NotValidType(Exception):
    def __init__(self, value, message="Invalid input value"):
        self.value = value
        self.message = message
        super().__init__(self.message)

TypeNameArray:list = ["nil", "boolean", "integer", "character", "string", "array", "set", "casting", "dynamic"]

class LanTypes(IntEnum):
    # Handlers #
    BREAK     = -1
    CONTINUE  = -2
    # Types #
    nil       = 0
    boolean   = 1
    integer   = 2
    character = 3
    string    = 4
    array     = 5
    set       = 6
    casting   = 7
    dynamic   = 8

    @staticmethod
    def is_valid_type(typeid:int):
        return (typeid <= 6) and (typeid >= 0)
    
    @staticmethod
    def is_indexable(typeid:int):
        return (typeid == LanTypes.array)
    
    @staticmethod
    def from_string(typestring:str) -> int:
        try: return TypeNameArray.index(typestring)
        except: return -1

    @staticmethod
    def to_string_name(typeid:int) -> str:
        return TypeNameArray[typeid]

class ParamChecker:
    @staticmethod
    def EnsureIntegrety(*params:tuple[VariableValue, int]) -> bool:
        for param in params:
            if param[1] != param[0].typeid: raise Exception(f"Type mismatch: Expected {param[1]}, got {param[0].typeid}.")
        return True
    
    @staticmethod
    def GetTypesOfParameters(*params:VariableValue) -> list[LanTypes]:
        Return = []
        for param in params:
            Return.append(param.typeid)
        return Return