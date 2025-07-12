# IMPORTS
import inspect

from memory import MemoryBooker

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
        return attribute(booker, *parmas)

    @staticmethod
    def dump_cache(booker:MemoryBooker, *params:any) -> None:
        for k, v in booker.Registry.items():
            print(f"{k} => {v[1].value}")

    @staticmethod
    def print(booker:MemoryBooker, *params:any) -> None:
        for param in list(params): print(param)

    @staticmethod
    def add(_, left:int, right: int) -> int:
        return left + right
    
    @staticmethod
    def input(_, prompt:str) -> str:
        return input(prompt)