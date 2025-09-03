# IMPORTS
import re

from lanregexes import ActualRegex
from lanerrors import LanErrors
from lantypes import VariableValue, LanTypes
from enum import IntEnum, StrEnum

class VarQuerryParts(StrEnum):
    AllMacthes = r"(?::[a-zA-Z]\w+)|(?:\[\d+\])"

# Runtime Memory Manager, aka Booker
class MemoryBooker:
    Registry:dict[str, VariableValue]
    FunctionRegistry:dict[str, any]
    ClassRegistry:dict[str, any]

    def __init__(this):
        from interpreter import LanFunction
        from lanclass import LanClass
        this.Registry = {}
        this.FunctionRegistry:dict[str, LanFunction] = {}
        this.ClassRegistry:dict[str, LanClass] = {}

    def set(this, varName:str, value:VariableValue, *flags:list[int]):
        this.Registry[varName] = value

    def get(this, varQuerry:str) -> VariableValue:
        if not this.find(varQuerry): raise LanErrors.MemoryMissingError(f"Could not find variable by name: {varQuerry}")
        m = ActualRegex.VariableStructure.value.match(varQuerry)
        varin:VariableValue = this.Registry[m.group(1)]
        if m.group(2):
            extention_m = re.findall(VarQuerryParts.AllMacthes, m.group(2), flags=re.UNICODE)
            for ext in extention_m:
                ext:str = ext
                if ext.startswith(':'):
                    rest:str = ext[1:]
                    if (varin.typeid == LanTypes.casting):
                        if (varin.value.has_method(':')):
                            varin = varin.value.do_method(':', [VariableValue(LanTypes.string, rest)])
                        else:
                            varin = varin.value.Properties[rest]
                    else:
                        varin = varin.value[rest]
                elif ext.startswith('[') and ext.endswith(']'):
                    varin = varin.value[int(ext[1:-1])]
                else: raise Exception("This is not a vaild indexing approch.")
        return varin
    
    def find(this, varQuerry:str) -> bool:
        m = ActualRegex.VariableStructure.value.match(varQuerry)
        return (m != None) and (m.group(1) in this.Registry.keys())

class VariableFlags(IntEnum):
    Protected = 1
    Global = 2