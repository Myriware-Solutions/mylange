# IMPORTS
import re

from lanregexes import ActualRegex
from lanerrors import LanErrors
from lantypes import VariableValue, LanTypes
from lanclass import LanClass, LanFunction
from enum import IntEnum, StrEnum

class VarQuerryParts(StrEnum):
    AllMacthes = r"(?::[a-zA-Z]\w+)|(?:\[\d+\])"

# Runtime Memory Manager, aka Booker
class MemoryBooker:
    Registry:dict[str, VariableValue]
    FunctionRegistry:dict[str, LanFunction]
    ClassRegistry:dict[str, LanClass]

    def __init__(self):
        from interpreter import LanFunction
        from lanclass import LanClass
        self.Registry = {}
        self.FunctionRegistry = {}
        self.ClassRegistry = {}

    def set(self, varName:str, value:VariableValue, *flags:list[int]):
        self.Registry[varName] = value

    def get(self, varQuerry:str) -> VariableValue:
        if not self.find(varQuerry): raise LanErrors.MemoryMissingError(f"Could not find variable by name: {varQuerry}")
        m = ActualRegex.VariableStructure.value.match(varQuerry); assert m is not None
        varin:VariableValue = self.Registry[m.group(1)]
        if m.group(2):
            extention_m = re.findall(VarQuerryParts.AllMacthes, m.group(2), flags=re.UNICODE)
            for ext in extention_m:
                assert varin is not None
                ext:str = ext
                if ext.startswith(':'):
                    rest:str = ext[1:]
                    if (varin.typeid == LanTypes.casting):
                        assert type(varin.value) is LanClass
                        if (varin.value.has_method(':')):
                            varin = varin.value.do_method(':', [VariableValue(LanTypes.string, rest)])
                        else:
                            try:
                                varin = varin.value.Properties[rest]
                            except KeyError:
                                raise LanErrors.NotIndexableError("Could not find this Property on object. Is it or colon-method private?")
                    else:
                        assert type(varin.value) is dict
                        varin = varin.value[rest]
                elif ext.startswith('[') and ext.endswith(']'):
                    index:int = int(ext[1:-1])
                    if (varin.typeid == LanTypes.casting):
                        assert type(varin.value) is LanClass
                        if (varin.value.has_method('[]')):
                            varin = varin.value.do_method('[]', [VariableValue(LanTypes.integer, index)])
                        else:
                            raise LanErrors.NotIndexableError("This class was not defined with a braket-index method, or that method is private.")
                    else:
                        assert type(varin.value) is list
                        varin = varin.value[index]
                else: raise Exception("This is not a vaild indexing approch.")
        return varin
    
    def find(self, varQuerry:str) -> bool:
        m = ActualRegex.VariableStructure.value.match(varQuerry)
        return (m != None) and (m.group(1) in self.Registry.keys())

class VariableFlags(IntEnum):
    Protected = 1
    Global = 2