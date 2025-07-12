from lantypes import VariableValue
from enum import IntEnum
# Runtime Memory Manager, aka Booker
class MemoryBooker:
    Registry:dict[str, tuple[int, VariableValue]]

    def echo(this, text:str, origin:str="Booker", indent:int=0) -> None:
        indentation:str = '\t'*indent
        print(f"{indentation}[{origin}] ", text)

    def __init__(this):
        this.Registry = {}

    def set(this, varName:str, value:VariableValue, *flags:list[int]):
        this.Registry[varName] = (sum(flags), value)
        this.echo(f"Set {varName} as {value}")

    def get(this, varName:str):
        return this.Registry[varName][1]
    
    def find(this, varName:str) -> bool:
        if varName in list(this.Registry.keys()): return True
        return False

class VariableFlags(IntEnum):
    Protected = 1
    Global = 2