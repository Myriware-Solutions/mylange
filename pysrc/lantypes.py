# IMPORTS
from enum import IntEnum, Enum
# Type castisting for variables

class VariableValue:
    typeid:int
    value:any
    def __init__(this, typeid:int):
        # if not LanTypes.is_valid_type(typeid):
        #     raise NotValidType()
        this.typeid = typeid

    def __str__(this):
        return f"<{this.value}@{this.typeid}>"

class RandomTypeConversions:
    @staticmethod
    def convert(string:str, mylangeInterpreter=None) -> any:
        typeid, other = RandomTypeConversions.get_type(string)
        match (typeid):
            case LanTypes.nil:
                return None
            case LanTypes.boolean if other == 0:
                return False
            case LanTypes.boolean if other == 1:
                return True
            case LanTypes.integer:
                return int(string)
            case LanTypes.character | LanTypes.string:
                return string[1:-1]
            case LanTypes.array:
                insides:str = string[1:-1]
                from interpreter import MylangeInterpreter, CodeCleaner
                mi:MylangeInterpreter = mylangeInterpreter
                parts:list[str] = [item.strip() for item in CodeCleaner.split_top_level_commas(insides)]
                r = [mi.format_parameter(item) for item in parts]
                return r
            case LanTypes.set:
                insides:str = string[1:-1]
                from interpreter import MylangeInterpreter, CodeCleaner
                mi:MylangeInterpreter = mylangeInterpreter
                parts:list[str] = [item.strip() for item in CodeCleaner.split_top_level_commas(insides)]
                Return:dict = {}
                for part in parts:
                    key_value = part.split('=>', 1)
                    Return[key_value[0]] = mi.format_parameter(key_value[1])
                return Return

    @staticmethod
    def get_type(string:str) -> tuple[int, int]:
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
        # String 
        if (string.startswith('"')) and (string.endswith('"')):
            return (LanTypes.string, 0)
        # Array 
        if (string.startswith('[')) and (string.endswith(']')):
            return (LanTypes.array, 0)
        # Set
        if (string.startswith('(')) and (string.endswith(')')):
            return (LanTypes.set, 0)
        
        # No value found, returning Nil
        return (LanTypes.nil, 0)

class NotValidType(Exception):
    def __init__(self, value, message="Invalid input value"):
        self.value = value
        self.message = message
        super().__init__(self.message)

TypeNameArray:list = ["nil", "boolean", "integer", "character", "string", "array", "set"]

class LanTypes(IntEnum):
    nil       = 0
    boolean   = 1
    integer   = 2
    character = 3
    string    = 4
    array     = 5
    set       = 6 #TODO: implement

    @staticmethod
    def is_valid_type(typeid:int):
        return (typeid <= 6) and (typeid >= 0)
    
    @staticmethod
    def is_indexable(typeid:int):
        return (typeid == LanTypes.array)
    
    @staticmethod
    def from_string(typestring:str) -> int:
        return TypeNameArray.index(typestring)

    @staticmethod
    def to_string_name(typeid:int) -> str:
        return TypeNameArray[typeid]