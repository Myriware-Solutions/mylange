# IMPORTS
import inspect

from memory import MemoryBooker
from lantypes import VariableValue, LanTypes

class MylangeBuiltinFunctions:
    @staticmethod
    def is_builtin(method_name:str) -> bool:
        if hasattr(MylangeBuiltinFunctions, method_name):
            attribute = getattr(MylangeBuiltinFunctions, method_name)
            return inspect.isfunction(attribute) or inspect.ismethod(attribute)
        return False
    @staticmethod
    def fire_builtin(booker:MemoryBooker, method_name:str, parmas:list) -> any:
        attribute = getattr(MylangeBuiltinFunctions, method_name)
        try:
            return attribute(booker, *parmas)
        except:
            print(*parmas)

    @staticmethod
    def dump_cache(booker:MemoryBooker, *params:any) -> None:
        for k, v in booker.Registry.items():
            print(f"{k} => {v[1].value} @ {v[1].typeid}")

    @staticmethod
    def print(_, *params:any) -> None:
        for param in list(params): print(param)

    @staticmethod
    def add(_, left:int, right: int) -> int:
        return left + right
    
    @staticmethod
    def input(_, prompt:str) -> str:
        return input(prompt)
    
class VariableTypeMethods:
    @staticmethod
    def get_type(i:int):
        match(i):
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
    def fire_variable_method(method:str, var:VariableValue, params:list) -> any:
        clazz = VariableTypeMethods.get_type(var.typeid)
        if VariableTypeMethods.is_applitable(var.typeid, method):
            attribute = getattr(clazz, method)
            return attribute(var, *params)
            # try:
            #     return attribute(*params)
            # except:
            #     print("Error occured for this method", *params)
        else: raise Exception(f"This method does not exist on this type: {method} @ {var.typeid}")

    class String:
        @staticmethod
        def charAt(var:VariableValue, index:int) -> str:
            return var.value[index]

    class Array:
        @staticmethod
        def concat(var:VariableValue, seperator:str=' ') -> str:
            return seperator.join(var.value)
        
        @staticmethod
        def append(var:VariableValue, *elements) -> None:
            l:list = var.value
            for ele in list(elements):
                l.append(ele)