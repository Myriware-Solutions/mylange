# IMPORTS
import re, copy, hashlib
from enum import IntFlag

from lantypes import LanType, LanScaffold, VariableValue, RandomTypeConversions
from lanerrors import LanErrors
from lanregexes import ActualRegex

import typing
if typing.TYPE_CHECKING:
    from interpreter import MylangeInterpreter
    
class AttributeAccessabilities(IntFlag):
    private = 1 << 0
    public  = 1 << 1
    static  = 1 << 2

# =========== #
#  Functions  #
# =========== #
class LanFunction:
    Name:str
    ReturnType:LanType
    Parameters:dict[str, LanType]
    Code:str
    Access:int
    MethodMasterClass:'LanClass|None' # If the function is acting as a method, provide it's master class
    def __init__(self, fName:str, fReturnType:LanType, fParamStruct:dict[str, LanType],
                 fCode:str, access=AttributeAccessabilities.public, methodMasterClass:'LanClass|None'=None):
        self.Parameters = fParamStruct
        self.Name = fName
        self.ReturnType = fReturnType
        self.Code = fCode
        self.Access = access
        self.MethodMasterClass = methodMasterClass
        
    @staticmethod
    def GetFunctionHash(name:str, paramTypes:list[LanType]) -> str:
        return re.sub(r"\s", "", f"{name}:" + ",".join([str(item) for item in paramTypes]))
    
    def execute(self, parent:'MylangeInterpreter', params:list[VariableValue],
                includeMemory:bool=False, flags:int=0) -> VariableValue:
        from interpreter import MylangeInterpreter
        container = MylangeInterpreter(f"Funct\\{self.Name}")
        old_mem_keys:list[str] = []
        if includeMemory:
            old_mem_keys = list(parent.Booker.Registry.keys())
        if (parent != None):
            if includeMemory: container.make_child_block(parent, True)
            else: container.make_child_block(parent, False)
            if parent.EchosEnables: container.enable_echos()
        container.echo(f"Executing LanFunction: {self.Name}; master: {self.MethodMasterClass}")
        # Add parameters
        if len(params) != len(self.Parameters):
            raise Exception(f"Length of Given and Expected Parameters do not Match: given {len(params)}, expected {len(self.Parameters)}")
        for i, param in enumerate(self.Parameters.items()):
            if (param[1] != LanScaffold.dynamic) and (params[i].Type != param[1]): 
                raise Exception(f"Parameter given and expected do not match types! Expected {param[1]}, given {params[i].Type}")
            container.Booker.set(param[0], params[i])
        Return = container.interpret(self.Code, True, self.MethodMasterClass, flags=flags)
        if Return is None:
            Return = VariableValue(LanType.nil())
        
        # Clear New Memory values, keeping old or altered ones
        if includeMemory: 
            for key in list(parent.Booker.Registry.keys()):
                if key not in old_mem_keys: del parent.Booker.Registry[key]
        if (self.ReturnType != LanScaffold.dynamic) and (Return.Type != self.ReturnType):
            raise LanErrors.WrongTypeExpectationError(f"Function \"{self.Name}\" is trying to return wrong value type. Expected '{self.ReturnType}', got '{Return.Type}'.")
        return Return
    
    def __str__(self) -> str:
        return f"def {self.ReturnType} {self.Name} ({", ".join([f"{key}: {tipe} " for key, tipe in self.Parameters.items()])})"
    
    def __repr__(self) -> str: return self.__str__()

# =========== #
#   Classes   #
# =========== #
class LanClass:
    Name:str
    Import:bool
    
    _methods_registry:dict[str, LanFunction]
    
    
    Properties:dict[str, VariableValue]
    PrivateProperties:dict[str, VariableValue]
    Parent:'MylangeInterpreter'
    @staticmethod
    def clean_code_block(codeBody:str) -> list[str]:
        r = re.sub(r"\n", '', codeBody, flags=re.MULTILINE|re.UNICODE)
        r = re.sub(r"^ +", '', r, flags=re.MULTILINE|re.UNICODE)
        r = re.sub(r" +", ' ', r, flags=re.MULTILINE|re.UNICODE)
        return r.split(';')
    def __str__(self):
        return "Class:" + self.Name
    def __init__(self, name:str, codeBody:str, parent:'MylangeInterpreter', imported:bool=False):
        self.Import = imported
        from interpreter import CodeCleaner
        # Setup defults
        self.Name = name
        self.Properties = {}; self.PrivateProperties = {}
        self._methods_registry = {}
        # Analyze code
        from interpreter import MylangeInterpreter
        self.Parent:MylangeInterpreter = parent
        codeBlockLines:str = parent.CleanCodeCache[codeBody.strip()]
        lines = LanClass.clean_code_block(codeBlockLines)
        #print(lines)
        property_strs = [ActualRegex.PropertyStatement.value.match(item) for item in lines if ActualRegex.PropertyStatement.value.search(item)]
        method_strs = [ActualRegex.ClassMethodStatement.value.match(item) for item in lines if ActualRegex.ClassMethodStatement.value.search(item)]
        # Assign Proproties
        for property_str in property_strs:
            assert property_str is not None
            parent.echo(f"[Classy] Working on line: {property_str.group(0)}")
            accessability = AttributeAccessabilities[property_str.group(1)]
            p_typeid = LanType.get_type_from_typestr(property_str.group(2))
            p_name = property_str.group(3)
            p_init = RandomTypeConversions.convert(property_str.group(4), parent) if (property_str.group(4)) else VariableValue(p_typeid, None)
            self.set_property(accessability, p_name, p_init)
        # Methods
        for method_str in method_strs:
            assert method_str is not None
            
            access = sum(AttributeAccessabilities[modifier] for modifier in re.findall(r"[\w]+", method_str.group(1)))
            
            method_params:dict[str, LanType]|None = None
            if access & AttributeAccessabilities.static: method_params = {}
            else: method_params = { "this": LanType(LanScaffold.this) }
            assert method_params is not None
            
            for method_param_str in CodeCleaner.split_top_level_commas(method_str.group(4), stripReturns=True):
                sections = CodeCleaner.split_top_level_commas(method_param_str, " ", stripReturns=True)
                if len(sections) != 2: raise Exception(f"Expected two parts from '{method_param_str}'")
                method_params[sections[1]] = LanType.get_type_from_typestr(sections[0])
            funct = LanFunction(method_str.group(3), 
                LanType.get_type_from_typestr(method_str.group(2)),
                method_params, parent.CleanCodeCache[method_str.group(5)], methodMasterClass=self)
            self.set_method(access, method_str.group(3), funct)
    
    def set_property(self, accessability:int, name:str, value:VariableValue):
        Group = None
        match accessability:
            case AttributeAccessabilities.private: Group = self.PrivateProperties
            case AttributeAccessabilities.public: Group = self.Properties
            case _: raise Exception()
        if name in Group.keys(): raise LanErrors.DuplicatePropertyError(name)
        Group[name] = value

    def set_method(self, access:int, name:str, funct:LanFunction) -> int:
        tup = LanFunction.GetFunctionHash(name, list(funct.Parameters.values()))
        funct.Access = access
        self._methods_registry[tup] = funct
        self.Parent.echo(f"Setting function: {name}, {access}, {funct}")
        return 0
    
    def get_method(self, name:str, paramTypes:list[LanType]) -> LanFunction:
        function_id = LanFunction.GetFunctionHash(name, paramTypes)
        self.Parent.echo(f"Getting method: {self._methods_registry}")
        if function_id not in self._methods_registry:
            raise LanErrors.NotIndexableError(f"Cannot find requested function '{function_id}' out of: {self._methods_registry.keys()}")
        return self._methods_registry[function_id]

    def create(self, args):
        object_copy = copy.deepcopy(self)
        object_copy.do_method("constructor", args, self)
        return VariableValue(LanType(LanScaffold.casting, ofClass=self.Name), object_copy)
    
    def props_to_set(self) -> VariableValue['LanClass']:
        full_properties = self.Properties | self.PrivateProperties
        return VariableValue(LanType.this(), self)
    
    def do_method(self, methodName:str, args:list[VariableValue], caller:'MylangeInterpreter|LanClass',
                  statically:bool=False, internalOverride:bool=False) -> VariableValue:
        full_parameters = [self.props_to_set()] + args
        method:LanFunction|None = None
        if statically: method = self.get_method(methodName, [arg.Type for arg in args])
        else: method = self.get_method(methodName, [arg.Type for arg in full_parameters])
        assert method is not None
        if (method.Access & AttributeAccessabilities.private):
            from interpreter import MylangeInterpreter
            if ((type(caller) is MylangeInterpreter) and (caller.ObjectMethodMaster is not None)
                and caller.ObjectMethodMaster.Name == self.Name): pass
            elif (type(caller) is LanClass) and caller.Name == self.Name: pass
            elif internalOverride: pass
            else: raise Exception("Cannot access this method. Are you internal?")
        Return = method.execute(self.Parent, full_parameters if not statically else args, False)
        self.Parent.echo(f"Doing method '{methodName}' with {full_parameters}")
        return Return if Return is not None else VariableValue(LanType.nil())
    
    def has_method(self, methodName:str, paramTypes:list[LanType]) -> bool:
        self.Parent.echo(f"Has method?: {LanFunction.GetFunctionHash(methodName, paramTypes)}")
        return LanFunction.GetFunctionHash(methodName, paramTypes) in self._methods_registry.keys()