# IMPORTS
import re
import copy
from enum import IntEnum

from lantypes import LanType, LanScaffold, VariableValue, RandomTypeConversions
from lanerrors import LanErrors
from lanregexes import ActualRegex

import typing
if typing.TYPE_CHECKING:
    from interpreter import MylangeInterpreter
# =========== #
#  Functions  #
# =========== #
class LanFunction:
    Name:str
    ReturnType:LanType
    Parameters:dict[str, LanType]
    Code:str
    def __init__(self, fName:str, fReturnType:LanType, fParamStruct:dict[str, LanType], fCode:str):
        self.Parameters = fParamStruct
        self.Name = fName
        self.ReturnType = fReturnType
        self.Code = fCode
    
    def execute(self, parent:'MylangeInterpreter', params:list[VariableValue], includeMemory:bool=False, objectMethodMaster:'LanClass|None'=None) -> VariableValue:
        from interpreter import MylangeInterpreter
        container = MylangeInterpreter(f"Funct\\{self.Name}")
        old_mem_keys:list[str] = []
        if includeMemory:
            old_mem_keys = list(parent.Booker.Registry.keys())
        if (parent != None):
            if includeMemory: container.make_child_block(parent, True)
            else: container.make_child_block(parent, False)
            if parent.EchosEnables: container.enable_echos()
        container.echo(f"Executing LanFunction: {self.Name}")
        # Add parameters
        if len(params) != len(self.Parameters):
            raise Exception(f"Length of Given and Expected Parameters do not Match: given {len(params)}, expected {len(self.Parameters)}")
        for i, param in enumerate(self.Parameters.items()):
            if (param[1] != LanScaffold.dynamic) and (params[i].Type != param[1]): 
                raise Exception(f"Parameter given and expected do not match types! Expected {param[1]}, given {params[i].Type}")
            container.Booker.set(param[0], params[i])
        Return = container.interpret(self.Code, True, objectMethodMaster)
        if Return is None:
            Return = VariableValue(LanType.nil())
        
        # Clear New Memory values, keeping old or altered ones
        if includeMemory: 
            for key in list(parent.Booker.Registry.keys()):
                if key not in old_mem_keys: del parent.Booker.Registry[key]
        if (self.ReturnType != LanScaffold.dynamic) and (Return.Type != self.ReturnType):
            raise LanErrors.WrongTypeExpectationError("Function is trying to return wrong value type.")
        return Return

class AttributeAccessabilities(IntEnum):
    private = 0
    public = 1

# =========== #
#   Classes   #
# =========== #
class LanClass:
    Name:str
    Methods:dict[str, LanFunction]
    PrivateMethods:dict[str, LanFunction]
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
        return self.Name
    def __init__(self, name:str, codeBody:str, parent:'MylangeInterpreter'):
        from interpreter import CodeCleaner
        # Setup defults
        self.Name = name
        self.Methods = {}; self.Properties = {}
        self.PrivateMethods = {}; self.PrivateProperties = {}
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
            accessability = AttributeAccessabilities[method_str.group(1)]
            method_params:dict[str, LanType] = { "this": LanType(LanScaffold.set) }
            for method_param_str in CodeCleaner.split_top_level_commas(method_str.group(4), stripReturns=True):
                sections = CodeCleaner.split_top_level_commas(method_param_str, " ", stripReturns=True)
                if len(sections) != 2: raise Exception(f"Expected two parts from '{method_param_str}'")
                method_params[sections[1]] = LanType.get_type_from_typestr(sections[0])
            funct = LanFunction(method_str.group(3), 
                LanType.get_type_from_typestr(method_str.group(2)),
                method_params, parent.CleanCodeCache[method_str.group(5)])
            self.set_method(accessability, method_str.group(3), funct)
    
    def set_property(self, accessability:AttributeAccessabilities, name:str, value:VariableValue):
        Group = None
        match accessability:
            case AttributeAccessabilities.private: Group = self.PrivateProperties
            case AttributeAccessabilities.public: Group = self.Properties
        if name in Group.keys(): raise LanErrors.DuplicatePropertyError(name)
        Group[name] = value

    def set_method(self, accessability:AttributeAccessabilities, name:str, funct:LanFunction):
        Group = None
        match accessability:
            case AttributeAccessabilities.private: Group = self.PrivateMethods
            case AttributeAccessabilities.public: Group = self.Methods
        if name in Group.keys(): raise LanErrors.DuplicateMethodError()
        Group[name] = funct

    def create(self, args):
        object_copy = copy.deepcopy(self)
        object_copy.do_method("constructor", args)
        return VariableValue(LanType(LanScaffold.casting), object_copy)
    
    def props_to_set(self) -> VariableValue:
        full_properties = self.Properties | self.PrivateProperties
        return VariableValue(LanType(LanScaffold.set), full_properties)
    
    def do_method(self, methodName:str, args:list[VariableValue]) -> VariableValue:
        full_parameters = [self.props_to_set()] + args
        Return = self.Methods[methodName].execute(self.Parent, full_parameters, False, self)
        self.Parent.echo(f"Doing method '{methodName}' with {full_parameters}")
        return Return if Return is not None else VariableValue(LanType.nil())
    
    def do_private_method(self, methodName, args) -> VariableValue:
        full_parameters = [self.props_to_set()] + args
        return self.PrivateMethods[methodName].execute(self.Parent, full_parameters, False, self)
    
    def has_method(self, methodName:str) -> bool:
        return methodName in self.Methods.keys()