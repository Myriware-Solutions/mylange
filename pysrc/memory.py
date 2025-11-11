# IMPORTS
import re

from lanregexes import ActualRegex
from lanerrors import LanErrors
from lantypes import VariableValue, LanType, LanScaffold
from lanclass import LanClass, LanFunction
from enum import IntEnum, StrEnum

class VarQuerryParts(StrEnum):
    AllMacthes = r"(?::[a-zA-Z]\w+)|(?:\[\d+\])"

# Runtime Memory Manager, aka Booker
class MemoryBooker:
    Registry:dict[str, VariableValue]
    _function_registry:dict[int, LanFunction]
    RegisteredFunctionNames:list[str]
    _class_registry:dict[str, LanClass]

    def __init__(self):
        from interpreter import LanFunction
        from lanclass import LanClass
        self.Registry = {}
        self._function_registry = {}
        self.RegisteredFunctionNames = []
        self._class_registry = {}
        
    @staticmethod
    def _get_function_hash(name:str, paramTypes:list[LanType]) -> int:
        return hash(tuple([name] + paramTypes))
    
    def SetFunction(self, name:str, funct:LanFunction) -> int:
        """Sets a function to the given name and function.

        Args:
            name (str): name of the function.
            funct (LanFunction): Object containing the function's data.

        Returns:
            int: Hash of the function, used in the registery.
        """
        if name not in self.RegisteredFunctionNames: self.RegisteredFunctionNames.append(name)
        tup = tuple([name] + list(funct.Parameters.values()))
        function_hash = hash(tup)
        self._function_registry[function_hash] = funct
        return function_hash
    
    def GetFunction(self, name:str, paramTypes:list[LanType]) -> LanFunction:
        function_id = self._get_function_hash(name, paramTypes)
        return self._function_registry[function_id]
    
    def SetClass(self, name:str, classStruct:LanClass) -> None:
        if name in self._class_registry: raise LanErrors.DuplicateMethodError(f"Class:{name}")
        self._class_registry[name] = classStruct
    
    def GetClass(self, name:str) -> LanClass:
        return self._class_registry[name]

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
                    if (varin.Type == LanScaffold.casting):
                        assert type(varin.value) is LanClass
                        if (varin.value.has_method(':')):
                            varin = varin.value.do_method(':', [VariableValue(LanType.string(), rest)])
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
                    if (varin.Type == LanScaffold.casting):
                        assert type(varin.value) is LanClass
                        if (varin.value.has_method('[]')):
                            varin = varin.value.do_method('[]', [VariableValue(LanType.int(), index)])
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