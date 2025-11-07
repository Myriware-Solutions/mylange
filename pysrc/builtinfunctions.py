# IMPORTS
import inspect

from importlib.metadata import version

from memory import MemoryBooker
from lantypes import VariableValue, ParamChecker, LanType, LanScaffold
from interface import AnsiColor
from lanclass import LanFunction, LanClass

NIL_RETURN:VariableValue = VariableValue(LanType.nil(), None)

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
    def load(_, filePath:VariableValue) -> VariableValue|None:
        from interpreter import MylangeInterpreter
        
        structure:MylangeInterpreter = MylangeInterpreter("Main")
        print("Found here")
        assert type(filePath.value) is str
        with open(filePath.value, mode="r", encoding='utf-8') as f:
            r = structure.interpret(f.read())
            return r
    
    @staticmethod
    def TypeOf(_, var:VariableValue, asString:VariableValue=VariableValue(LanType.bool(), False)) -> VariableValue:
        if asString.value == True:
            return VariableValue(LanType.string(), str(var.Type))
        else: return VariableValue(LanType.int(), var.Type.TypeNum)

    class Casting(MylangeBuiltinScaffold):
        @staticmethod
        def PrintoutDetails(booker:MemoryBooker, castingVariable:VariableValue, isNameOfType:VariableValue=VariableValue(LanType.bool(), False)) -> None:
            assert type(castingVariable.value) is str
            casting = booker.ClassRegistry[castingVariable.value] if (isNameOfType.value == True) else castingVariable.value
            assert type(casting) is LanClass
            print("== System.IO.PrintoutDetails =="*AnsiColor.BRIGHT_BLUE)
            #:dict[str, dict[str, dict[str, VariableValue|LanFunction]]]
            a:dict[str, dict[str, dict[str, VariableValue]] | dict[str, dict[str, LanFunction]]] = {
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
                print(f"[{attribute_type}]"*AnsiColor.BRIGHT_BLUE)
                for accessability, items in attr_info.items():
                    for name, item in items.items():
                        say:str=""
                        match attribute_type:
                            case "Properties":
                                assert type(item) is VariableValue
                                say = f"{accessability} {LanScaffold.TypeNameArray()[item.Type.TypeNum]} {name}" 
                            case "Methods":
                                assert type(item) is LanFunction
                                say = f"{accessability} {item.ReturnType} {name} ({(", ".join([f"{itype} {iname}" for iname, itype in item.Parameters.items()]))})"
                        print(say*AnsiColor.BRIGHT_BLUE)
            print("==            End            =="*AnsiColor.BRIGHT_BLUE)

    class Set(MylangeBuiltinScaffold):
        @staticmethod
        def Assign(_, setObject:VariableValue, key:VariableValue, value:VariableValue):
            assert type(key.value) is str
            setObjectDict = setObject.value; assert type(setObjectDict) is dict[str, VariableValue]
            setObjectDict[key.value] = value
        
    class System(MylangeBuiltinScaffold):
        @staticmethod
        def Version(_) -> None:
            print(f"Mylange Version: {(version("mylange"))}"*AnsiColor.BRIGHT_BLUE)
        
        class IO(MylangeBuiltinScaffold):
            @staticmethod
            def DumpCache(booker:MemoryBooker) -> None:
                print("== :System.IO.DumpCache =="*AnsiColor.BRIGHT_BLUE)
                items = booker.Registry.items() | booker.FunctionRegistry.items() | booker.ClassRegistry.items()
                for k, v in items:
                    match v:
                        case VariableValue():
                            print(f"{k} @ {v.Type} => {v}"*AnsiColor.BRIGHT_BLUE)
                        case LanClass():
                            print(f"class {k}"*AnsiColor.BRIGHT_BLUE)
                        case LanFunction():
                            print(f"function {k}"*AnsiColor.BRIGHT_BLUE)
                print("==         End          =="*AnsiColor.BRIGHT_BLUE)
            @staticmethod
            def Input(_, prompt:VariableValue) -> VariableValue:
                return VariableValue(LanType.string(), input(prompt.value))
            @staticmethod
            def Println(_, *params:VariableValue) -> None:
                for param in list(params): print(param.to_string())

        class File(MylangeBuiltinScaffold):

            @staticmethod
            def Read(_, fileName:VariableValue) -> VariableValue:
                file_name = fileName.value; assert type(file_name) is str
                with open(file_name, 'r', encoding="utf-8") as f:
                    return VariableValue(LanType.string(), f.read())
            
            @classmethod
            def Execute(cls, _, fileName:VariableValue) -> VariableValue|None:
                content = cls.Read(None, fileName)
                from interpreter import MylangeInterpreter
                virtual_engine = MylangeInterpreter("SysExe")
                assert type(content.value) is str
                return virtual_engine.interpret(content.value)

class VariableTypeMethods:
    @staticmethod
    def get_type(i:LanScaffold):
        match(i):
            case LanScaffold.integer:
                return VariableTypeMethods.Integer
            case LanScaffold.string:
                return VariableTypeMethods.String
            case LanScaffold.array:
                return VariableTypeMethods.Array
            case LanScaffold.set:
                return VariableTypeMethods.Set
            
    @staticmethod
    def is_applitable(typeid:int, method_name:str) -> bool:
        clazz = VariableTypeMethods.get_type(LanScaffold(typeid))
        if hasattr(clazz, method_name):
            attribute = getattr(clazz, method_name)
            return inspect.isfunction(attribute) or inspect.ismethod(attribute)
        return False
    
    @staticmethod
    def fire_variable_method(parent, method:str, var:VariableValue, params:list[VariableValue]) -> VariableValue:
        if (var.Type.TypeNum > -1):
            # Mylange Class
            clazz = VariableTypeMethods.get_type(var.Type.TypeNum)
            if VariableTypeMethods.is_applitable(var.Type.TypeNum, method):
                attribute = getattr(clazz, method)
                return attribute(parent, var, *params)
            else: raise Exception(f"This method does not exist on this type: {method} @ {var.Type}")
        else:
            # User Defined Class
            assert type(var.value) is LanClass
            return var.value.do_method(method, params)

    class Integer:
        # Add a number to the variable,
        # returning a reference to the variable
        @staticmethod
        def add(_, var:VariableValue[int], amount:VariableValue[int]) -> VariableValue[int]:
            var.value = var.value + amount.value
            return var

        @staticmethod
        def toString(_, var:VariableValue[int]) -> VariableValue:
            return VariableValue[str](LanType.string(), f"{var.value}")
        
    class String:
        # Use:
        # Returns a character at the index in the string.
        # chatAt(integar index)
        # index: (integar) The index to get the character at.
        @staticmethod
        def charAt(_, var:VariableValue, index:VariableValue) -> VariableValue:
            return VariableValue(LanType.string(), var.value[index.value])
        
        # Use: 
        # Returns or alters a string containing replacement indicators--%s--with the
        # arguments passed into the function.
        # String.format(string replacements...)
        # String.format(boolean desctructive, string replacements...)
        @staticmethod
        def format(_, var:VariableValue, destructive:VariableValue=VariableValue(LanType.bool(), False), 
                   *replacements:VariableValue) -> VariableValue:
            Return:str = var.value + ""
            if not destructive.isof(LanType.bool()):
                Return = Return.replace(f'%s', str(destructive.value), 1)
            for replacement in replacements:
                Return = Return.replace(f'%s', str(replacement.value), 1)
            if destructive.isof(LanType.bool()) and (destructive.value == True):
                var.value = Return
                return NIL_RETURN
            return VariableValue(LanType.string(), Return)
        
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
                    destructive:VariableValue=VariableValue(LanType.bool(), False)) -> VariableValue:
            replaced_string:str = var.value.replace(old.value, new.value, 1)
            if destructive.value:
                var.value = replaced_string
                return NIL_RETURN
            return VariableValue(LanType.string(), replaced_string)
        
        # Use:
        # Replaces all or a specified amount of instances of a string.
        # replace(string old, string new, integar? limit, boolean? destructive)
        # old: (string) The value to look for and will be replaced
        # new: (string) The value that will be put in the old's place
        # [limit]: (int?) The amount of instances to replace. If the value is -1 (default), then all instances are replaced.
        # [desctructive]: (boolean?) Optional. Whether or not to modify the existing string, or return a new one.
        @staticmethod
        def replaceAll(_, var:VariableValue, old:VariableValue, new:VariableValue, 
                       limit:VariableValue=VariableValue(LanType.int(), -1),
                       destructive:VariableValue=VariableValue(LanType.bool(), False) ) -> VariableValue:
            replaced_string:str = var.value.replace(old.value, new.value, limit.value)
            if destructive.value:
                var.value = replaced_string
                return NIL_RETURN
            return VariableValue(LanType.string(), replaced_string)
        
        # Splits a string into smaller strings, on the characher seperator
        # String.split(character sep)
        # sep: (character) The character to sperate the string on.
        # returns: an array of the strings seperated by sep
        @staticmethod
        def split(_, var:VariableValue[str], sep:VariableValue[str]) -> VariableValue[list[VariableValue]]:
            ParamChecker.EnsureIntegrety((sep, LanType.char()))
            string:str = var.value
            val = [VariableValue(LanType.string(), part) for part in string.split(sep.value)]
            return VariableValue(LanType.array(), val)
    
        @staticmethod
        def toCharArray(_, var:VariableValue) -> VariableValue:
            string:str = var.value
            Return = []
            for char in string:
                Return.append(VariableValue(LanType.char(), char))
            return VariableValue(LanType.array(), Return)

        @staticmethod
        def toInteger(_, var:VariableValue) -> VariableValue:
            return VariableValue(LanType.int(), int(var.value))
    
    class Array:
        @staticmethod
        def at(_, var:VariableValue, index:VariableValue) -> VariableValue:
            ParamChecker.EnsureIntegrety((index, LanType.int()))
            return var.value[index.value]

        @staticmethod
        def concat(_, var:VariableValue, sep:VariableValue[str]=VariableValue[str](LanType.string(), " ")) -> VariableValue:
            return VariableValue(LanType.string(), sep.value.join([item.to_string() for item in var.value]))
        
        @staticmethod
        def append(_, var:VariableValue, *elements:VariableValue) -> VariableValue:
            l = var.value
            if type(l) is not list: raise Exception(f"Wrong type to be appending (SHOULD NOT OCCURE)! Expected list, got {type(l)}")
            for ele in list(elements):
                if var.Type.Archetype and (ele.Type not in var.Type): raise Exception(f"Trying to append element of incorrect Type. Expected {var.Type.Archetype}, got {ele.Type}")
                l.append(ele)
            return NIL_RETURN

        # Use:
        # .where(function callback, array additional)
        # callback: (function) A function that takes one parameter, and returns a boolean value of some evaluation.
        # [params]: (array?) Any values that should be passed into the function that would not be found locally within the function.
        @staticmethod
        def where(parent, var:VariableValue, callback:LanFunction, paramsArray:VariableValue=VariableValue(LanType.array(), [])) -> VariableValue:
            if callback.ReturnType != LanType.bool(): raise Exception("This function cannot be used, as it does not return boolean.")
            items:list[VariableValue] = var.value
            params:list[VariableValue] = paramsArray.value
            Return = []
            for item in items:
                valid:VariableValue = callback.execute(parent, [item] + params)
                if valid.value: Return.append(item)
            return VariableValue(LanType.array(), Return)
        
        @staticmethod
        def find(parent, var:VariableValue, callback:LanFunction, paramsArray:VariableValue) -> VariableValue:
            whereArray = VariableTypeMethods.Array.where(parent, var, callback, paramsArray).value
            assert type(whereArray) is list[VariableValue]
            Result = True if len(whereArray) > 0 else False
            return VariableValue(LanType.bool(), Result)
        
        @staticmethod
        def length(_, var:VariableValue) -> VariableValue:
            assert type(var.value) is list
            return VariableValue(LanType.int(), len(var.value))
        
        @staticmethod
        def indexOf(_, var:VariableValue[list[VariableValue]], item:VariableValue) -> VariableValue[int]:
            array = var.value
            for i, aitem in enumerate(array):
                if aitem.value == item.value:
                    return VariableValue[int](LanType.int(), i)
            return VariableValue[int](LanType.int(), -1)
        
        # Destructivly alters an array and adds a range from [begining, end) into it, returning a reference to it.
        @staticmethod
        def makeRange(_, var:VariableValue, end:VariableValue, begining:VariableValue=VariableValue(LanType.int(), 0)) -> VariableValue:
            r = [VariableValue(LanType.int(), i) for i in list(range(begining.value, end.value))]
            var.value.extend(r)
            return var
        
        # Returns an array of ararys, containing the [0] index and the [1] value.
        # Optionally, it will start on the provided start index.
        # Array.enumerate(integer? start)
        @staticmethod
        def enumerate(_, var:VariableValue, start:VariableValue=VariableValue(LanType.int(), 0)) -> VariableValue:
            ParamChecker.EnsureIntegrety((start, LanType.int()))
            items:list[VariableValue] = var.value
            Return = []
            for i, item in enumerate(items, start.value):
                Return.append(VariableValue(LanType.array(), [VariableValue(LanType.int(), i), item]))
            return VariableValue(LanType.array(), Return)
        
        @staticmethod
        def has(_, var:VariableValue, item:VariableValue) -> VariableValue:
            
            return VariableValue(LanType.bool(), 1)
    
    class Set:
        @staticmethod
        def assign(_, setObject:VariableValue, key:VariableValue, value:VariableValue) -> VariableValue:
            
            setObjectDict = setObject.value; assert type(setObjectDict) is dict
            assert type(key.value) is str
            if setObject.Type.Archetype and (value.Type not in setObject.Type): raise Exception("YKYK")
            setObjectDict[key.value] = value
            return NIL_RETURN

        @staticmethod
        def at(_, var:VariableValue, index:VariableValue) -> VariableValue:
            ParamChecker.EnsureIntegrety((index, LanType.string()))
            return var.value[index.value]
        
        @staticmethod
        def keys(_, var:VariableValue) -> VariableValue:
            Return = [VariableValue(LanType.string(), key) for key in var.value.keys()]
            return VariableValue(LanType.array(), Return)
        
        @staticmethod
        def values(_, var:VariableValue) -> VariableValue:
            Return = var.value.values()
            return VariableValue(LanType.array(), Return)
        
        @staticmethod
        def pairs(_, var:VariableValue):
            Return = []
            for k, v in var.value.items():
                Return.append(VariableValue(LanType.array(), [VariableValue(LanType.string(), k), v]))
            return VariableValue(LanType.array(), Return)

