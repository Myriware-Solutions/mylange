# IMPORTS
from enum import IntEnum, Enum
# Type castisting for variables

class VariableValue:
    typeid:int
    value:any
    def __init__(this, typeid:int):
        # if not LanTypes.is_valid_type(typeid):
        #     raise LanTypeErrors.NotValidType
        this.typeid = typeid

    def from_string(this, string:str):
        match (this.typeid):
            case LanTypes.boolean:
                if (string in ["true", "True", "t", "T", "yes", "Yes"]):
                    this.value = True
                elif (string in ["false", "False", "f", "F", "no", "No"]):
                    this.value = False
                else:
                    raise Exception(f"Boolean does not parse: {string}")
            case LanTypes.integer:
                try:
                    this.value = int(string)
                except:
                    raise Exception(f"Integer does not parse: {string}")
            case LanTypes.string:
                if (string.startswith('"')) and (string.endswith('"')):
                    this.value = string[1:-1]
                else:
                    raise Exception(f"String does not parse: {string}")
                    

    def to_boolean(this):
        pass 

    def to_integer(this):
        pass

    def to_string(this):
        pass

class LanTypeErrors(Enum):
    class NotValidType(Exception):
        def __init__(self, value, message="Invalid input value"):
            self.value = value
            self.message = message
            super().__init__(self.message)

class LanTypes(IntEnum):
    boolean = 1
    integer = 2
    string  = 3
    @staticmethod
    def is_valid_type(typeid:int):
        return typeid < 2
    
    @staticmethod
    def from_string(typestring:str) -> int:
        match (typestring):
            case "boolean": return 1
            case "integer": return 2
            case "string": return 3