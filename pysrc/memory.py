# IMPORTS
import re

from lanregexes import LanRe
from lanerrors import LanErrors
from lantypes import VariableValue
from enum import IntEnum, StrEnum

class VarQuerryParts(StrEnum):
    AllMacthes = r"(?::[a-zA-Z]\w+)|(?:\[\d+\])"

# Runtime Memory Manager, aka Booker
class MemoryBooker:
    Registry:dict[str, tuple[int, VariableValue]]

    def __init__(this):
        this.Registry = {}

    def set(this, varName:str, value:VariableValue, *flags:list[int]):
        this.Registry[varName] = (sum(flags), value)

    def get(this, varQuerry:str) -> VariableValue:
        if not this.find(varQuerry): raise LanErrors.MemoryMissingError(f"Could not find variable by name: {varQuerry}")
        m = re.match(LanRe.VariableStructure, varQuerry)
        varin = this.Registry[m.group(1)][1]
        if m.group(2):
            extention_m = re.findall(VarQuerryParts.AllMacthes, m.group(2))
            for ext in extention_m:
                ext:str = ext
                if ext.startswith(':'):
                    varin = varin.value[ext[1:]]
                elif ext.startswith('[') and ext.endswith(']'):
                    varin = varin.value[int(ext[1:-1])]
                else: raise Exception("This is not a vaild indexing approch.")
        return varin
    
    def find(this, varQuerry:str) -> bool:
        m = re.match(LanRe.VariableStructure, varQuerry)
        #if not m: raise LanErrors.MemoryMissingError(f"Could not find variable by name: {varQuerry}")
        return (m != None) and (m.group(1) in this.Registry.keys())

class VariableFlags(IntEnum):
    Protected = 1
    Global = 2