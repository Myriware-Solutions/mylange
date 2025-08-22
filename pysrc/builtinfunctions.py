# IMPORTS
import inspect

from memory import MemoryBooker
from lantypes import VariableValue, LanTypes
from interface import AnsiColor
from lanclass import LanFunction

NIL_RETURN:VariableValue = VariableValue(LanTypes.nil, None)


def EnsureIntegrety(*params:tuple[VariableValue, int]) -> bool:
    for param in params:
        if param[1] != param[0].typeid: return False
    return True

def GetTypesOfParameters(*params:VariableValue) -> list[LanTypes]:
    Return = []
    for param in params:
        Return.append(param.typeid)
    return Return

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
    def print(_, *params:VariableValue) -> None:
        for param in list(params): print(param.to_string())
    
    @staticmethod
    def input(_, prompt:VariableValue) -> VariableValue:
        return VariableValue(LanTypes.string, input(prompt.value))
    
    @staticmethod
    def set_assign(_, setObject:VariableValue, key:VariableValue, value:VariableValue):
        setObjectDict:dict[str, VariableValue] = setObject.value
        setObjectDict[key.value] = value
    
    @staticmethod
    def load(_, filePath:VariableValue) -> VariableValue:
        from interpreter import MylangeInterpreter
        structure:MylangeInterpreter = MylangeInterpreter("Main")
        print("Found here")
        with open(filePath.value, "r", encoding='utf-8') as f:
            r = structure.interpret(f.read())
            return r
    
class VariableTypeMethods:
    @staticmethod
    def get_type(i:int):
        match(i):
            case LanTypes.integer:
                return VariableTypeMethods.Intager
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
    def fire_variable_method(parent, method:str, var:VariableValue, params:list[VariableValue]) -> VariableValue:
        if (var.typeid > -1):
            # Mylange Class
            clazz = VariableTypeMethods.get_type(var.typeid)
            if VariableTypeMethods.is_applitable(var.typeid, method):
                attribute = getattr(clazz, method)
                return attribute(parent, var, *params)
            else: raise Exception(f"This method does not exist on this type: {method} @ {var.typeid}")
        else:
            # User Defined Class
            return var.value.do_method(method, params)

    class Intager:
        # Add a number to the variable,
        # returning a reference to the variable
        @staticmethod
        def add(_, var:VariableValue, amount:VariableValue) -> None:
            var.value = var.value + amount.value
            return var

        @staticmethod
        def toString(_, var:VariableValue) -> VariableValue:
            return VariableValue(LanTypes.string, f"{var.value}")

    class String:
        # Use:
        # Returns a character at the index in the string.
        # chatAt(integar index)
        # index: (integar) The index to get the character at.
        @staticmethod
        def charAt(_, var:VariableValue, index:VariableValue) -> VariableValue:
            return VariableValue(LanTypes.string, var.value[index.value])
        
        @staticmethod
        def format(_, var:VariableValue, destructive:VariableValue=VariableValue(LanTypes.boolean, False), 
                   *replacements:VariableValue) -> VariableValue:
            Return:str = var.value + ""
            for replacement in replacements:
                Return = Return.replace(f'%s', replacement.value, 1)
            if destructive.value:
                var.value = Return
                return NIL_RETURN
            return VariableValue(LanTypes.string, Return)
        
        # Use:
        # Replaces the first instance of the found string.
        # replace(string old, string new, boolean? destructive)
        # old: (string) The value to look for and will be replaced
        # new: (string) The value that will be put in the old's place
        # [desctructive]: (boolean?) Optional. Whether or not to modify the existing string, or return a new one.
        @staticmethod
        def replace(_, var:VariableValue, old:VariableValue, new:VariableValue, 
                    destructive:VariableValue=VariableValue(LanTypes.boolean, False)) -> VariableValue:
            replaced_string:str = var.value.replace(old.value, new.value, 1)
            if destructive.value:
                var.value = replaced_string
                return NIL_RETURN
            return VariableValue(LanTypes.string, replaced_string)
        
        # Use:
        # Replaces all or a specified amount of instances of a string.
        # replace(string old, string new, integar? limit, boolean? destructive)
        # old: (string) The value to look for and will be replaced
        # new: (string) The value that will be put in the old's place
        # [limit]: (int?) The amount of instances to replace. If the value is -1 (default), then all instances are replaced.
        # [desctructive]: (boolean?) Optional. Whether or not to modify the existing string, or return a new one.
        @staticmethod
        def replaceAll(_, var:VariableValue, old:VariableValue, new:VariableValue, 
                       limit:VariableValue=VariableValue(LanTypes.integer, -1),
                       destructive:VariableValue=VariableValue(LanTypes.boolean, False) ) -> VariableValue:
            replaced_string:str = var.value.replace(old.value, new.value, limit.value)
            if destructive.value:
                var.value = replaced_string
                return NIL_RETURN
            return VariableValue(LanTypes.string, replaced_string)
        
        @staticmethod
        def print(_, var:VariableValue) -> None:
            print(var)
            
    class Array:
        @staticmethod
        def concat(_, var:VariableValue, seperator:VariableValue=None) -> VariableValue:
            seperator:str = seperator.value if seperator != None else ' '
            return VariableValue(LanTypes.string, seperator.join([item.to_string() for item in var.value]))
        
        @staticmethod
        def append(_, var:VariableValue, *elements) -> None:
            l:list = var.value
            for ele in list(elements):
                l.append(ele)
            return NIL_RETURN

        # Use:
        # .where(function callback, array additional)
        # callback: (function) A function that takes one parameter, and returns a boolean value of some evaluation.
        # [params]: (array?) Any values that should be passed into the function that would not be found locally within the function.
        @staticmethod
        def where(parent, var:VariableValue, callback:LanFunction, paramsArray:VariableValue=VariableValue(LanTypes.array, [])) -> VariableValue:
            if callback.ReturnType != LanTypes.boolean: raise Exception("This function cannot be used, as it does not return boolean.")
            items:list[VariableValue] = var.value
            params:list[VariableValue] = paramsArray.value
            Return = []
            for item in items:
                valid:VariableValue = callback.execute(parent, [item] + params)
                if valid.value: Return.append(item)
            return VariableValue(LanTypes.array, Return)
        
        @staticmethod
        def find(parent, var:VariableValue, callback:LanFunction, paramsArray:VariableValue) -> VariableValue:
            whereArray:list[VariableValue] = VariableTypeMethods.Array.where(parent, var, callback, paramsArray).value
            Result = True if len(whereArray) > 0 else False
            return VariableValue(LanTypes.boolean, Result)
        
        @staticmethod
        def length(_, var:VariableValue) -> VariableValue:
            return VariableValue(LanTypes.integer, len(var.value))
        
        @staticmethod
        def indexOf(_, var:VariableValue, item:VariableValue) -> VariableValue:
            array:list[VariableValue] = var.value
            i:int = 0
            for aitem in array:
                if aitem.value == item.value:
                    return VariableValue(LanTypes.integer, i)
                i += 1
            return VariableValue(LanTypes.integer, -1)
        
        # Destructivly alters an array and adds a range from [begining, end) into it, returning a reference to it.
        @staticmethod
        def makeRange(_, var:VariableValue, end:VariableValue, begining:VariableValue=VariableValue(LanTypes.integer, 0)) -> VariableValue:
            r = [VariableValue(LanTypes.integer, i) for i in list(range(begining.value, end.value))]
            var.value.extend(r)
            return var
