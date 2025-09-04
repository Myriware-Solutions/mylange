# IMPORTS
import re
import copy
from enum import IntEnum

from lantypes import LanTypes, VariableValue, RandomTypeConversions
from lanerrors import LanErrors
from lanregexes import ActualRegex
# =========== #
#  Functions  #
# =========== #
class LanFunction:
    Name:str
    ReturnType:int
    Parameters:dict[str,int]
    Code:str
    def __init__(this, fName:str, fReturnType:str, fParamString:str, fCode:str):
        this.Parameters = {}
        this.Name = fName
        this.ReturnType = LanTypes.from_string(fReturnType)
        try:
            for set in fParamString.split(","):
                if set == "": continue
                set_parts = set.strip().split(" ")
                this.Parameters[set_parts[1]] = LanTypes.from_string(set_parts[0])
        except IndexError:
            raise Exception("Fatal Error: Params Expected and Given missmatch: ")
        this.Code = fCode
    
    def execute(this, parent:any, params:list[VariableValue], includeMemory:bool=False, objectMethodMaster:'LanClass'=None) -> VariableValue:
        from interpreter import MylangeInterpreter
        parent:MylangeInterpreter = parent
        container = MylangeInterpreter(f"Funct\\{this.Name}")
        old_mem_keys:list[str] = []
        if includeMemory:
            old_mem_keys = list(parent.Booker.Registry.keys())
        if (parent != None):
            if includeMemory: container.make_child_block(parent, True)
            else: container.make_child_block(parent, False)
            if parent.EchosEnables: container.enable_echos()
        # Add parameters
        if len(params) != len(this.Parameters):
            raise Exception(f"Length of Given and Expected Parameters do not Match: given {len(params)}, expected {len(this.Parameters)}")
        for i, param in enumerate(this.Parameters.items()):
            if (param[1] != LanTypes.dynamic) and (params[i].typeid != param[1]): raise Exception(f"Parameter given and expected do not match types! Expected {param[1]}, given {params[i].typeid}")
            container.Booker.set(param[0], params[i])
        Return:VariableValue = container.interpret(this.Code, True, objectMethodMaster)
        # Clear New Memory values, keeping old or altered ones
        if includeMemory: 
            for key in list(parent.Booker.Registry.keys()):
                if key not in old_mem_keys: del parent.Booker.Registry[key]
        if (this.ReturnType != LanTypes.dynamic) and (Return.typeid != this.ReturnType):
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
    Parent:any
    @staticmethod
    def clean_code_block(codeBody:str) -> list[str]:
        r = re.sub(r"\n", '', codeBody, flags=re.MULTILINE|re.UNICODE)
        r = re.sub(r"^ +", '', r, flags=re.MULTILINE|re.UNICODE)
        r = re.sub(r" +", ' ', r, flags=re.MULTILINE|re.UNICODE)
        return r.split(';')
    def __str__(this):
        return this.Name
    def __init__(this, name:str, codeBody:str, parent:any):
        # Setup defults
        this.Name = name
        this.Methods = {}; this.Properties = {}
        this.PrivateMethods = {}; this.PrivateProperties = {}
        # Analyze code
        from interpreter import MylangeInterpreter
        parent:MylangeInterpreter = parent
        this.Parent:MylangeInterpreter = parent
        codeBlockLines:str = parent.CleanCodeCache[codeBody.strip()]
        lines = LanClass.clean_code_block(codeBlockLines)
        #print(lines)
        property_strs:list[re.Match[str]] = [ActualRegex.PropertyStatement.value.match(item) for item in lines if ActualRegex.PropertyStatement.value.search(item)]
        method_strs:list[re.Match[str]] = [ ActualRegex.ClassMethodStatement.value.match(item) for item in lines if ActualRegex.ClassMethodStatement.value.search(item)]
        # Assign Proproties
        for property_str in property_strs:
            parent.echo(f"[Classy] Working on line: {property_str.group(0)}")
            accessability = AttributeAccessabilities[property_str.group(1)]
            p_typeid = LanTypes.from_string(property_str.group(2))
            p_name = property_str.group(3)
            p_init = RandomTypeConversions.convert(property_str.group(4)) if (property_str.group(4)) else VariableValue(p_typeid, None)
            this.set_property(accessability, p_name, p_init)
        # Methods
        for method_str in method_strs:
            accessability = AttributeAccessabilities[method_str.group(1)]
            init_param_str = ",".join(["set this"] + method_str.group(4).split(','))
            funct = LanFunction(method_str.group(3), method_str.group(2), init_param_str, parent.CleanCodeCache[method_str.group(5)])
            this.set_method(accessability, method_str.group(3), funct)
    
    def set_property(this, accessability:AttributeAccessabilities, name:str, value:VariableValue):
        Group = None
        match accessability:
            case AttributeAccessabilities.private: Group = this.PrivateProperties
            case AttributeAccessabilities.public: Group = this.Properties
        if name in Group.keys(): raise LanErrors.DuplicatePropertyError(name)
        Group[name] = value

    def set_method(this, accessability:AttributeAccessabilities, name:str, funct:LanFunction):
        Group = None
        match accessability:
            case AttributeAccessabilities.private: Group = this.PrivateMethods
            case AttributeAccessabilities.public: Group = this.Methods
        if name in Group.keys(): raise LanErrors.DuplicateMethodError()
        Group[name] = funct

    def create(this, args):
        object_copy = copy.deepcopy(this)
        object_copy.do_method("constructor", args)
        return VariableValue(LanTypes.casting, object_copy)
    
    def props_to_set(this) -> VariableValue:
        full_properties = this.Properties | this.PrivateProperties
        return VariableValue(LanTypes.set, full_properties)
    
    def do_method(this, methodName:str, args:list[VariableValue]) -> VariableValue:
        full_parameters = [this.props_to_set()] + args
        return this.Methods[methodName].execute(this.Parent, full_parameters, False, this)
    
    def do_private_method(this, methodName, args) -> VariableValue:
        full_parameters = [this.props_to_set()] + args
        return this.PrivateMethods[methodName].execute(this.Parent, full_parameters, False, this)
    
    def has_method(this, methodName:str) -> bool:
        return methodName in this.Methods.keys()