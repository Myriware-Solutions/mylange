# IMPORTS
import inspect

from memory import MemoryBooker
from lantypes import VariableValue, LanTypes, RandomTypeConversions
from interface import AnsiColor

class MylangeBuiltinFunctions:
    @staticmethod
    def is_builtin(method_name:str) -> bool:
        if hasattr(MylangeBuiltinFunctions, method_name):
            attribute = getattr(MylangeBuiltinFunctions, method_name)
            return inspect.isfunction(attribute) or inspect.ismethod(attribute)
        return False
    @staticmethod
    def fire_builtin(booker:MemoryBooker, method_name:str, params:list[VariableValue]) -> any:
        attribute = getattr(MylangeBuiltinFunctions, method_name)
        try:
            return attribute(booker, *params)
        except:
            print(*params)

    @staticmethod
    def dump_cache(booker:MemoryBooker) -> None:
        for k, v in booker.Registry.items():
            AnsiColor.println(f"{k} @ {v.typeid} => {v}", AnsiColor.BRIGHT_BLUE)

    @staticmethod
    def print(_, *params:any) -> None:
        for param in list(params): print(param.to_string())
    
    @staticmethod
    def input(_, prompt:VariableValue) -> str:
        return input(prompt.value)
    
class VariableTypeMethods:
    @staticmethod
    def get_type(i:int):
        match(i):
            case LanTypes.integer:
                return VariableTypeMethods.Interger
            case LanTypes.string:
                return VariableTypeMethods.String
            case LanTypes.array:
                return VariableTypeMethods.Array
            
    @staticmethod
    def is_applitable(typeid:int, method_name:str) -> bool:
        clazz = VariableTypeMethods.get_type(typeid)
        if hasattr(clazz, method_name):
            attribute = getattr(clazz, method_name)
            return inspect.isfunction(attribute) or inspect.ismethod(attribute)
        return False
    
    @staticmethod
    def fire_variable_method(method:str, var:VariableValue, params:list[VariableValue]) -> any:
        if (var.typeid > -1):
            # Mylange Class
            clazz = VariableTypeMethods.get_type(var.typeid)
            if VariableTypeMethods.is_applitable(var.typeid, method):
                attribute = getattr(clazz, method)
                return attribute(var, *params)
            else: raise Exception(f"This method does not exist on this type: {method} @ {var.typeid}")
        else:
            # User Defined Class
            return var.value.do_method(method, params)

    class Interger:
        @staticmethod
        def add(var:VariableValue, amount:VariableValue) -> None:
            var.value = var.value + amount.value

        @staticmethod
        def toString(var:VariableValue) -> VariableValue:
            return VariableValue(LanTypes.string, f"{var.value}")

    class String:
        @staticmethod
        def charAt(var:VariableValue, index:VariableValue) -> VariableValue:
            return VariableValue(LanTypes.string, var.value[index.value])

    class Array:
        @staticmethod
        def concat(var:VariableValue, seperator:VariableValue=None) -> VariableValue:
            seperator:str = seperator.value if seperator != None else ' '
            return VariableValue(LanTypes.string, seperator.join([item.to_string() for item in var.value]))
        
        @staticmethod
        def append(var:VariableValue, *elements) -> None:
            l:list = var.value
            for ele in list(elements):
                l.append(ele)