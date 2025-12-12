# IMPORTS
from enum import IntEnum, Enum, unique, auto
from lanregexes import ActualRegex
import re
from typing import Generic, TypeVar

from lanerrors import LanErrors

T = TypeVar("T")
#type VariableValueLike = None|bool|int|str|list['VariableValue']|dict[str,'VariableValue']|'LanClass'

import typing
if typing.TYPE_CHECKING:
    from lanclass import LanClass, LanFunction
    from interpreter import MylangeInterpreter

# Type castisting for variables

class RandomTypeConversions:
    @staticmethod
    def convert(string:str, mylangeInterpreter:'MylangeInterpreter') -> 'VariableValue':
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
                return VariableValue(LanType.string(), string[1:-1])
            
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
            
            case LanScaffold.callback:
                from lanclass import LanFunction
                parsed = mylangeInterpreter.format_parameter(string)
                if type(parsed) is not LanFunction:
                    raise LanErrors.WrongTypeExpectationError("Expected a function, got: "+str(parsed))
                return VariableValue(LanType.callback(), parsed)
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
    this      = 9
    callback  = 10
    
    @classmethod
    def from_string(cls, typestring:str) -> 'LanScaffold':
        for i, aliases in enumerate(cls.TypeNameArray()):
            if typestring in aliases: return LanScaffold(i)
        raise LanErrors.UnknownTypeError(typestring)

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
            ["dynamic"],
            ["this"],
            ["callback"],
            ["union"]
        ]
    
class LanType:
    
    TypeNum:LanScaffold
    Archetype:'list[LanType]|None'
    OfClass:str|None = None
    
    def __init__(self, typeNum:LanScaffold, archetype:'list[LanType]|None'=None, ofClass:str|None=None) -> None:
        self.TypeNum = typeNum
        self.Archetype = archetype
        self.OfClass = ofClass
        # Casting's need to be attached to a class they are of.
        if self.TypeNum == LanScaffold.casting:
            if ofClass is None: raise Exception("Casting types must have a class attached to them.")
    
    def __eq__(self, other:object) -> bool:
        if type(other) is LanType:
            if self.TypeNum.value != other.TypeNum.value: return False
            if (self.TypeNum.value == LanScaffold.casting) and \
                (self.OfClass != other.OfClass): return False
            if (self.Archetype is None) and (other.Archetype is None): return True
            else: 
                if (self.Archetype is None) and (other.Archetype is not None) or \
                    (self.Archetype is not None) and (other.Archetype is None): return False
                assert self.Archetype is not None; assert other.Archetype is not None
                if len(self.Archetype) != len(other.Archetype): return False
                for i, archtypette in enumerate(self.Archetype):
                    if archtypette != other.Archetype[i]: return False
            return True
        elif type(other) is LanScaffold:
            return self.TypeNum.value == other.value
        else: raise Exception(f"Cannot compare these types! Expected {type(self)}, got {type(other)}")
    
    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)
    
    def __contains__(self, item:object) -> bool:
        if type(item) is not LanType: raise Exception(f"Cannot use that type: {type(item)}")
        if not self.Archetype: return False
        return item in self.Archetype
    
    def __str__(self) -> str:
        if self.TypeNum == LanScaffold.casting:
            return f"casting({self.OfClass})"
        return f"{LanScaffold.TypeNameArray()[self.TypeNum][0]}" + (f"<{"|".join(str(g) for g in self.Archetype)}>" if self.Archetype else "")
    
    def __hash__(self) -> int:
        return hash(tuple(item for item in (([self.TypeNum] + self.Archetype) if self.Archetype else [self.TypeNum])))
    
    # def __repr__(self) -> str:
    #     return self.__str__()
    
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
    def string(): return LanType(LanScaffold.string)
    
    @staticmethod
    def array(): return LanType(LanScaffold.array)
    
    @staticmethod
    def set(): return LanType(LanScaffold.set)
    
    @staticmethod
    def this(): return LanType(LanScaffold.this)
    
    @staticmethod
    def callback(): return LanType(LanScaffold.callback)
    
    @classmethod
    def get_type_from_typestr(cls, string:str) -> 'LanType':
        reg = re.compile(r"(\w+)\s?(?:<([\w<>\s|,]+)>)?")
        m = reg.match(string); assert m is not None
        ofClass:str|None=None
        try: base = LanScaffold.from_string(m.group(1))
        except LanErrors.UnknownTypeError:
            # It did not find a Mylange class, but it could be user-defined
            base = LanScaffold.casting
            ofClass=string.strip()
        if m.group(2):
            from interpreter import CodeCleaner
            archetypette_strs = CodeCleaner.split_top_level_commas(m.group(2))
            l:list[LanType] = []
            for archetypette_str in archetypette_strs:
                l.append(cls.get_type_from_typestr(archetypette_str))
            return LanType(base, l)
        else: return LanType(base, ofClass=ofClass)
    
    @classmethod
    def make_param_type_dict(cls, string:str) -> dict[str, 'LanType']:
        #reg = re.compile(r"(?:([\w<>\s|,]+))?\s+(\w+)")
        reg = re.compile(r"([\w ]+[\w<>,| ]+) +(\w+)", flags=re.UNICODE)
        Return:dict[str, LanType] = {}
        from interpreter import CodeCleaner
        entries = CodeCleaner.split_top_level_commas(string, additionalBrackets=[('<','>')])
        for entry in entries:
            m = reg.match(entry.strip()); assert m is not None
            Return[m.group(2)] = cls.get_type_from_typestr(m.group(1))
        return Return

class ParamChecker:
    @staticmethod
    def EnsureIntegrety(*params:tuple['VariableValue', LanType]) -> bool:
        for param, ex_type in params:
            if param.Type != ex_type: return False
        return True

    @staticmethod
    def GetTypesOfParameters(*params:'VariableValue') -> list[LanType]:
        Return = []
        for param in params:
            Return.append(param.Type)
        return Return



class VariableValue(Generic[T]):
    Type:LanType
    def __init__(self, typeStruct:LanType, value:T=None):
        self.Type = typeStruct
        self.value = value

    def __str__(self, withPrefix:bool=False):
        Return = ""
        match (self.Type.TypeNum):
            case LanScaffold.nil:
                Return = 'nil'
            case LanScaffold.boolean:
                Return= f"{self.value}".lower()
            case LanScaffold.integer:
                Return= f"{self.value}"
            case LanScaffold.character:
                Return= f"'{self.value}'"
            case LanScaffold.string:
                Return= f'"{self.value}"'
            case LanScaffold.array:
                assert type(self.value) is list
                larray = [f"{item}" for item in self.value]
                Return= f"[{', '.join(larray)}]"
            case LanScaffold.set:
                assert type(self.value) is dict
                lset = [f"{k}:{v}" for k, v in self.value.items()]
                Return= f"({', '.join(lset)})"
            case _:
                Return= f"<{self.value}@{self.Type}>"
        if withPrefix: return f"{str(self.Type)} {Return}"
        return Return
    
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
        ParamChecker.EnsureIntegrety((self, LanType(LanScaffold.set)))
        assert type(self.value) is dict
        return self.value[index]

    def bracket_access(self, index:int) -> 'VariableValue':
        ParamChecker.EnsureIntegrety((self, LanType(LanScaffold.array)))
        assert type(self.value) is list
        return self.value[index]