# IMPORTS
import inspect

from importlib.metadata import version

from memory import MemoryBooker
from lantypes import VariableValue, LanTypes, ParamChecker, TypeNameArray
from interface import AnsiColor
from lanclass import LanFunction, LanClass

NIL_RETURN:VariableValue = VariableValue(LanTypes.nil, None)

class MylangeBuiltinScaffold:
    @classmethod
    def is_builtin(cls, class_method_path:list[str]):
        return cls.get_method(class_method_path) != None
    @classmethod
    def get_method(cls, class_method_path:list[str]):
        first:str = class_method_path[0]
        if hasattr(cls, first):
            attribute = getattr(cls, first)
            if inspect.isfunction(attribute) or inspect.ismethod(attribute):
                return attribute
            elif isinstance(attribute, type):
                return attribute.get_method(class_method_path[1:])
        return None


class MylangeBuiltinFunctions(MylangeBuiltinScaffold):
    @staticmethod
    def print(_, *params:VariableValue) -> None:
        for param in list(params): print(param.to_string())
    
    @staticmethod
    def load(_, filePath:VariableValue) -> VariableValue:
        from interpreter import MylangeInterpreter
        
        structure:MylangeInterpreter = MylangeInterpreter("Main")
        print("Found here")
        with open(filePath.value, mode="r", encoding='utf-8') as f:
            r = structure.interpret(f.read())
            return r
        
    def TypeOf(_, var:VariableValue, asString:VariableValue=VariableValue(LanTypes.boolean, False)) -> VariableValue:
        if asString.value: return VariableValue(LanTypes.string, TypeNameArray[var.typeid])
        else: return VariableValue(LanTypes.integer, var.typeid)

    class Casting(MylangeBuiltinScaffold):
        @staticmethod
        def PrintoutDetails(booker:MemoryBooker, castingVariable:VariableValue, isNameOfType:VariableValue=VariableValue(LanTypes.boolean, False)) -> None:
            casting = booker.ClassRegistry[castingVariable.value] if (isNameOfType.value == True) else castingVariable.value
            assert type(casting) is LanClass
            print("== System.IO.PrintoutDetails =="*AnsiColor.BRIGHT_BLUE)
            a:dict[str, dict[str, dict[str, VariableValue|LanFunction]]] = {
                "Properties": {
                    "public": casting.Properties,
                    "private": casting.PrivateProperties
                },
                "Methods": {
                    "public": casting.Methods,
                    "private": casting.PrivateMethods
                }
            }
            
            for attribute_type, attr_info in a.items():
                AnsiColor.println(f"[{attribute_type}]", AnsiColor.BRIGHT_BLUE)
                for accessability, items in attr_info.items():
                    for name, item in items.items():
                        say:str = None
                        match attribute_type:
                            case "Properties": say = f"{accessability} {TypeNameArray[item.typeid]} {name}" 
                            case "Methods": say = f"{accessability} {TypeNameArray[item.ReturnType]} {name} ({(", ".join([f"{TypeNameArray[itype]} {iname}" for iname, itype in item.Parameters.items()]))})"
                        AnsiColor.println(say, AnsiColor.BRIGHT_BLUE)
            AnsiColor.println("==            End            ==", AnsiColor.BRIGHT_BLUE)

    class Set(MylangeBuiltinScaffold):
        @staticmethod
        def Assign(_, setObject:VariableValue, key:VariableValue, value:VariableValue):
            setObjectDict:dict[str, VariableValue] = setObject.value
            setObjectDict[key.value] = value
        
    class System(MylangeBuiltinScaffold):
        @staticmethod
        def Version(_) -> None:
            AnsiColor.println(f"Mylange Version: {(version("mylange"))}", AnsiColor.BRIGHT_BLUE)
        
        class IO(MylangeBuiltinScaffold):
            @staticmethod
            def DumpCache(booker:MemoryBooker) -> None:
                AnsiColor.println("== :System.IO.DumpCache ==", AnsiColor.BRIGHT_BLUE)
                items = booker.Registry.items() | booker.FunctionRegistry.items() | booker.ClassRegistry.items()
                for k, v in items:
                    match v:
                        case VariableValue():
                            AnsiColor.println(f"{k} @ {v.typeid} => {v}", AnsiColor.BRIGHT_BLUE)
                        case LanClass():
                            AnsiColor.println(f"class {k}", AnsiColor.BRIGHT_BLUE)
                        case LanFunction():
                            AnsiColor.println(f"function {k}", AnsiColor.BRIGHT_BLUE)
                AnsiColor.println("==         End          ==", AnsiColor.BRIGHT_BLUE)
            @staticmethod
            def Input(_, prompt:VariableValue) -> VariableValue:
                return VariableValue(LanTypes.string, input(prompt.value))
            @staticmethod
            def Println(_, *params:VariableValue) -> None:
                for param in list(params): print(param.to_string())

        class File(MylangeBuiltinScaffold):

            @staticmethod
            def Read(_, fileName:VariableValue) -> VariableValue:
                file_name:str = fileName.value
                with open(file_name, 'r', encoding="utf-8") as f:
                    return VariableValue(LanTypes.string, f.read())
            
            @classmethod
            def Execute(this, _, fileName:VariableValue) -> VariableValue:
                content = this.Read(None, fileName)
                from interpreter import MylangeInterpreter
                virtual_engine = MylangeInterpreter("SysExe")
                return virtual_engine.interpret(content.value)

    
class VariableTypeMethods:
    @staticmethod
    def get_type(i:int):
        match(i):
            case LanTypes.integer:
                return VariableTypeMethods.Integer
            case LanTypes.string:
                return VariableTypeMethods.String
            case LanTypes.array:
                return VariableTypeMethods.Array
            case LanTypes.set:
                return VariableTypeMethods.Set
            
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

    class Integer:
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
        
        # Use: 
        # Returns or alters a string containing replacement indicators--%s--with the
        # arguments passed into the function.
        # String.format(string replacements...)
        # String.format(boolean desctructive, string replacements...)
        @staticmethod
        def format(_, var:VariableValue, destructive:VariableValue=VariableValue(LanTypes.boolean, False), 
                   *replacements:VariableValue) -> VariableValue:
            Return:str = var.value + ""
            if not destructive.isof(LanTypes.boolean):
                Return = Return.replace(f'%s', str(destructive.value), 1)
            for replacement in replacements:
                Return = Return.replace(f'%s', str(replacement.value), 1)
            if destructive.isof(LanTypes.boolean) and (destructive.value == True):
                var.value = Return
                return NIL_RETURN
            return VariableValue(LanTypes.string, Return)
        
        @staticmethod
        def print(_, var:VariableValue) -> None:
            print(var)
        
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
        
        # Splits a string into smaller strings, on the characher seperator
        # String.split(character sep)
        # sep: (character) The character to sperate the string on.
        # returns: an array of the strings seperated by sep
        @staticmethod
        def split(_, var:VariableValue, sep:VariableValue) -> VariableValue:
            ParamChecker.EnsureIntegrety((sep, LanTypes.character))
            string:str = var.value
            val = [VariableValue(LanTypes.string, part) for part in string.split(sep.value)]
            return VariableValue(LanTypes.array, val)
    
        @staticmethod
        def toCharArray(_, var:VariableValue) -> VariableValue:
            string:str = var.value
            Return = []
            for char in string:
                Return.append(VariableValue(LanTypes.character, char))
            return VariableValue(LanTypes.array, Return)

        @staticmethod
        def toInteger(_, var:VariableValue) -> VariableValue:
            return VariableValue(LanTypes.integer, int(var.value))
    
    class Array:
        @staticmethod
        def at(_, var:VariableValue, index:VariableValue) -> VariableValue:
            ParamChecker.EnsureIntegrety((index, LanTypes.integer))
            return var.value[index.value]

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
        
        # Returns an array of ararys, containing the [0] index and the [1] value.
        # Optionally, it will start on the provided start index.
        # Array.enumerate(integer? start)
        @staticmethod
        def enumerate(_, var:VariableValue, start:VariableValue=VariableValue(LanTypes.integer, 0)) -> VariableValue:
            ParamChecker.EnsureIntegrety((start, LanTypes.integer))
            items:list[VariableValue] = var.value
            Return = []
            for i, item in enumerate(items, start.value):
                Return.append(VariableValue(LanTypes.array, [VariableValue(LanTypes.integer, i), item]))
            return VariableValue(LanTypes.array, Return)
    
    class Set:
        @staticmethod
        def assign(_, setObject:VariableValue, key:VariableValue, value:VariableValue) -> VariableValue:
            setObjectDict:dict[str, VariableValue] = setObject.value
            setObjectDict[key.value] = value
            return NIL_RETURN

        @staticmethod
        def at(_, var:VariableValue, index:VariableValue) -> VariableValue:
            ParamChecker.EnsureIntegrety((index, LanTypes.string))
            return var.value[index.value]
        
        @staticmethod
        def keys(_, var:VariableValue) -> VariableValue:
            Return = [VariableValue(LanTypes.string, key) for key in var.value.keys()]
            return VariableValue(LanTypes.array, Return)
        
        @staticmethod
        def values(_, var:VariableValue) -> VariableValue:
            Return = var.value.values()
            return VariableValue(LanTypes.array, Return)
        
        @staticmethod
        def pairs(_, var:VariableValue):
            Return = []
            for k, v in var.value.items():
                Return.append(VariableValue(LanTypes.array, [VariableValue(LanTypes.string, k), v]))
            return VariableValue(LanTypes.array, Return)

