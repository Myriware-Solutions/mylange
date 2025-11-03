# IMPORTS
from enum import IntEnum, Enum
from lanregexes import ActualRegex
import re

import typing
if typing.TYPE_CHECKING:
    from lanclass import LanClass

# Type castisting for variables

class VariableValue:
    type VariableValueLike = None|bool|int|str|list['VariableValue']|dict[str,'VariableValue']|'LanClass'
    typeid:int
    def __init__(self, typeid:int, value:VariableValueLike=None):
        self.typeid = typeid
        self.value:VariableValue.VariableValueLike = None
        if (value != None): self.value = value

    def __str__(self):
        match (self.typeid):
            case LanTypes.nil:
                return 'nil'
            case LanTypes.boolean:
                return f"{self.value}".lower()
            case LanTypes.integer:
                return f"{self.value}"
            case LanTypes.character:
                return f"'{self.value}'"
            case LanTypes.string:
                return f'"{self.value}"'
            case LanTypes.array:
                assert type(self.value) is list
                larray = [f"{item}" for item in self.value]
                return f"[{', '.join(larray)}]"
            case LanTypes.set:
                assert type(self.value) is dict
                lset = [f"{k}:{v}" for k, v in self.value.items()]
                return f"({', '.join(lset)})"
        return f"<{self.value}@{self.typeid}>"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def isof(self, type:int) -> bool:
        return self.typeid == type
    
    def to_string(self):
        match (self.typeid):
            case LanTypes.boolean:
                return f"{self.value}".lower()
            case LanTypes.integer:
                return f"{self.value}"
            case LanTypes.character | LanTypes.string:
                return self.value
            case _:
                return self.__str__()
            
    def colon_access(self, index:str) -> 'VariableValue':
        from builtinfunctions import ParamChecker
        ParamChecker.EnsureIntegrety((self, LanTypes.set))
        assert type(self.value) is dict
        return self.value[index]

    def bracket_access(self, index:int) -> 'VariableValue':
        from builtinfunctions import ParamChecker
        ParamChecker.EnsureIntegrety((self, LanTypes.array))
        assert type(self.value) is list
        return self.value[index]

class RandomTypeConversions:
    @staticmethod
    def convert(string:str, mylangeInterpreter) -> VariableValue:
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
            case _:
                raise Exception("Typeid is Unkown.")

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

TypeNameArray:list[list[str]] = [
    ["nil"],
    ["boolean", "bool"],
    ["integer", "int"],
    ["character", "char"], 
    ["string", "str"], 
    ["array", "arr"], 
    ["set"], 
    ["casting"], 
    ["dynamic"]]

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
        for i, aliases in enumerate(TypeNameArray):
            if typestring in aliases: return i
        return -1

    @staticmethod
    def to_string_name(typeid:int) -> str:
        return TypeNameArray[typeid][0]

class ParamChecker:
    @staticmethod
    def EnsureIntegrety(*params:tuple[VariableValue, int]) -> bool:
        for param in params:
            if param[1] != param[0].typeid: raise Exception(f"[Type Validation] Type mismatch: Expected {TypeNameArray[param[1]]}, got {TypeNameArray[param[0].typeid]}.")
        return True
    
    @staticmethod
    def GetTypesOfParameters(*params:VariableValue) -> list[LanTypes]:
        Return = []
        for param in params:
            Return.append(param.typeid)
        return Return