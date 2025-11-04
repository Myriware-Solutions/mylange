# IMPORTS
from enum import IntEnum, Enum, unique
from lanregexes import ActualRegex
import re

import typing
if typing.TYPE_CHECKING:
    from lanclass import LanClass

# Type castisting for variables

class RandomTypeConversions:
    @staticmethod
    def convert(string:str, mylangeInterpreter) -> 'VariableValue':
        typeid, other = RandomTypeConversions.get_type(string)
        match (typeid):
            case LanScaffold.nil:
                return VariableValue(LanType.nil(), None)
            case LanScaffold.boolean if other == 0:
                return VariableValue(LanType.bool(), False)
            case LanScaffold.boolean if other == 1:
                return VariableValue(LanType.bool(), True)
            case LanScaffold.integer:
                return VariableValue(LanType.int(), int(string))
            case LanScaffold.character:
                return VariableValue(LanType.char(), string[1:-1])
            case LanScaffold.string:
                return VariableValue(LanType.str(), string[1:-1])
            
            case LanScaffold.array:
                insides:str = string[1:-1]
                from interpreter import MylangeInterpreter, CodeCleaner
                mi:MylangeInterpreter = mylangeInterpreter
                parts:list[str] = [item.strip() for item in CodeCleaner.split_top_level_commas(insides)]
                ReturnL:list = []
                ArchetypeTypeIds:list[LanType] = []
                for item in parts:
                    var = mi.format_parameter(item)
                    assert type(var) is VariableValue
                    ReturnL.append(var)
                    if var.Type not in ArchetypeTypeIds: 
                        ArchetypeTypeIds.append(var.Type)
                return VariableValue(LanType(LanScaffold.array, ArchetypeTypeIds), ReturnL)
            
            case LanScaffold.set:
                insides:str = string[1:-1]
                from interpreter import MylangeInterpreter, CodeCleaner
                mi:MylangeInterpreter = mylangeInterpreter
                parts:list[str] = [item.strip() for item in CodeCleaner.split_top_level_commas(insides)]
                ReturnS:dict = {}
                ArchetypeTypeIds:list[LanType] = []
                for part in parts:
                    key_value = part.split('=>', 1)
                    var = mi.format_parameter(key_value[1])
                    assert type(var) is VariableValue
                    ReturnS[key_value[0].strip()] = var
                    if var.Type not in ArchetypeTypeIds: 
                        ArchetypeTypeIds.append(var.Type)
                return VariableValue(LanType(LanScaffold.set, ArchetypeTypeIds), ReturnS)
            case _:
                raise Exception("Typeid is Unkown.")

    @staticmethod
    def get_type(string:str) -> tuple['LanScaffold', int]:
        # nil
        if (string == 'nil'):
            return (LanScaffold.nil, 0)
        # boolean 
        if (string == "true"):
            return (LanScaffold.boolean, 1)
        elif (string == "false"):
            return (LanScaffold.boolean, 0)
        # Int 
        try:
            _ = int(string)
            return (LanScaffold.integer, 0)
        except: pass
        # Character
        if (string.startswith("'")) and (string.endswith("'")):
            return (LanScaffold.character, 0)
        # String 
        if (string.startswith('"')) and (string.endswith('"')):
            return (LanScaffold.string, 0)
        # Array 
        if (string.startswith('[')) and (string.endswith(']')):
            return (LanScaffold.array, 0)
        # Set
        if (string.startswith('(')) and (string.endswith(')')):
            if re.search(ActualRegex.SetInners.value, string) or re.search(r"\(\s*\)", string):
                return (LanScaffold.set, 0)
            else: return (LanScaffold.nil, 0)
        # No value found, returning Nil
        return (LanScaffold.nil, 0)

class NotValidType(Exception):
    def __init__(self, value, message="Invalid input value"):
        self.value = value
        self.message = message
        super().__init__(self.message)

@unique
class LanScaffold(IntEnum):
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
    
    @classmethod
    def from_string(cls, typestring:str) -> int:
        for i, aliases in enumerate(cls.TypeNameArray()):
            if typestring in aliases: return i
        return -1

    @classmethod
    def to_string_name(cls, typeid:int) -> str:
        return cls.TypeNameArray()[typeid][0]
    
    @staticmethod
    def TypeNameArray() -> list[list[str]]:
        return [
            ["nil"],
            ["boolean", "bool"],
            ["integer", "int"],
            ["character", "char"], 
            ["string", "str"], 
            ["array", "arr"], 
            ["set"], 
            ["casting"], 
            ["dynamic"]
        ]
    
class LanType():
    
    TypeNum:LanScaffold
    Archetype:'list[LanType]|None'
    
    def __init__(self, typeNum:LanScaffold, archetype:'list[LanType]|None'=None) -> None:
        self.TypeNum = typeNum
        self.Archetype = archetype
    
    def __eq__(self, other:object) -> bool:
        if type(other) is not LanType: raise Exception("Cannot compare these types!")
        if self.TypeNum.value != other.TypeNum.value: return False
        if (self.Archetype is None) and (other.Archetype is None): return True
        assert self.Archetype is not None; assert other.Archetype is not None
        if len(self.Archetype) != len(other.Archetype): return False
        for i, archtypette in enumerate(self.Archetype):
            if archtypette != other.Archetype[i]: return False
        return True
    
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    
    def __str__(self) -> str:
        return f"{LanScaffold.TypeNameArray()[self.TypeNum]}" + (f"<{self.Archetype}>" if self.Archetype else "")
    
    # Static types that are always the same
    @staticmethod
    def nil(): return LanType(LanScaffold.nil)
    
    @staticmethod
    def bool(): return LanType(LanScaffold.boolean)
    
    @staticmethod
    def int(): return LanType(LanScaffold.integer)
    
    @staticmethod
    def char(): return LanType(LanScaffold.character)
    
    @staticmethod
    def str(): return LanType(LanScaffold.string)

class ParamChecker:
    @staticmethod
    def EnsureIntegrety(*params:tuple['VariableValue', int]) -> bool:
        # for param in params:
        #     if param[1] != param[0].typeid: 
        #         raise Exception(f"[Type Validation] Type mismatch: Expected {LanScaffold.TypeNameArray()[param[1]]}, got {LanScaffold.TypeNameArray()[param[0].typeid]}.")
        return True

    @staticmethod
    def GetTypesOfParameters(*params:'VariableValue') -> list[LanType]:
        Return = []
        for param in params:
            Return.append(param.Type)
        return Return

class VariableValue:
    type VariableValueLike = None|bool|int|str|list['VariableValue']|dict[str,'VariableValue']|'LanClass'
    Type:LanType
    def __init__(self, typeStruct:LanType, value:VariableValueLike=None):
        self.Type = typeStruct
        self.value:VariableValue.VariableValueLike = None
        if (value != None): self.value = value

    def __str__(self):
        match (self.Type.TypeNum):
            case LanScaffold.nil:
                return 'nil'
            case LanScaffold.boolean:
                return f"{self.value}".lower()
            case LanScaffold.integer:
                return f"{self.value}"
            case LanScaffold.character:
                return f"'{self.value}'"
            case LanScaffold.string:
                return f'"{self.value}"'
            case LanScaffold.array:
                assert type(self.value) is list
                larray = [f"{item}" for item in self.value]
                return f"[{', '.join(larray)}]"
            case LanScaffold.set:
                assert type(self.value) is dict
                lset = [f"{k}:{v}" for k, v in self.value.items()]
                return f"({', '.join(lset)})"
        return f"<{self.value}@{self.Type}>"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def isof(self, type:LanType) -> bool:
        return self.Type == type
    
    def to_string(self):
        match (self.Type.TypeNum):
            case LanScaffold.boolean:
                return f"{self.value}".lower()
            case LanScaffold.integer:
                return f"{self.value}"
            case LanScaffold.character | LanScaffold.string:
                return self.value
            case _:
                return self.__str__()
            
    def colon_access(self, index:str) -> 'VariableValue':
        ParamChecker.EnsureIntegrety((self, LanScaffold.set))
        assert type(self.value) is dict
        return self.value[index]

    def bracket_access(self, index:int) -> 'VariableValue':
        ParamChecker.EnsureIntegrety((self, LanScaffold.array))
        assert type(self.value) is list
        return self.value[index]