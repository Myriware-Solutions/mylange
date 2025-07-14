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

    def from_string(this, string:str):
        match (this.typeid):
            case LanTypes.boolean:
                if (string in ["true", "True", "t", "T", "yes", "Yes"]):
                    this.value = True
                elif (string in ["false", "False", "f", "F", "no", "No"]):
                    this.value = False
            case LanTypes.integer:
                try:
                    this.value = int(string)
                except: pass
            case LanTypes.string:
                if (string.startswith('"')) and (string.endswith('"')):
                    this.value = string[1:-1]
        this.value = None

class RandomTypeConversions:
    @staticmethod
    def convert(string:str, mylangeInterpreter=None) -> any:
        typeid, other = RandomTypeConversions.get_type(string)
        match (typeid):
            case 0:
                return None
            case 1 if other == 0:
                return False
            case 1 if other == 1:
                return True
            case 2:
                return int(string)
            case 3:
                return string[1:-1]
            case 4:
                insides:str = string[1:-1]
                from interpreter import MylangeInterpreter, CodeCleaner
                mi:MylangeInterpreter = mylangeInterpreter
                parts:list[str] = [item.strip() for item in CodeCleaner.split_top_level_commas(insides)]
                r = [mi.format_parameter(item) for item in parts]
                return r


    @staticmethod
    def get_type(string:str) -> tuple[int, int]:
        # Boolean Found
        if (string == "true"):
            return (1, 1)
        elif (string == "false"):
            return (1, 0)
        # Int Found
        try:
            _ = int(string)
            return (2, 0)
        except: pass
        # String Found
        if (string.startswith('"')) and (string.endswith('"')):
            return (3, 0)
        # Array Found
        if (string.startswith('[')) and (string.endswith(']')):
            return (4, 0)
        
        # No value found, returning Nil
        return (0, 0)

class NotValidType(Exception):
    def __init__(self, value, message="Invalid input value"):
        self.value = value
        self.message = message
        super().__init__(self.message)

class LanTypes(IntEnum):
    nil     = 0
    boolean = 1
    integer = 2
    string  = 3
    array   = 4
    lset    = 5 #TODO: implement

    @staticmethod
    def is_valid_type(typeid:int):
        return typeid < 2
    
    @staticmethod
    def from_string(typestring:str) -> int:
        match (typestring):
            case "boolean": return 1
            case "integer": return 2
            case "string": return 3
            case "array": return 4