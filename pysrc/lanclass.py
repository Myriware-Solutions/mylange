# IMPORTS
import re
import copy

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
        r:VariableValue = None
        throw_break = False
        try: 
            r = container.interpret(this.Code, True, objectMethodMaster)
        except LanErrors.Break: throw_break = True
        # Clear New Memory values, keeping old or altered ones
        if includeMemory: 
            for key in list(parent.Booker.Registry.keys()):
                if key not in old_mem_keys: del parent.Booker.Registry[key]
        if throw_break: raise LanErrors.Break()
        return r

# =========== #
#   Classes   #
# =========== #
class LanClass:
    Name:str
    Methods:dict[str, LanFunction]
    Properties:dict[str, VariableValue]
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
        this.Methods = {}
        this.Properties = {}
        # Analyze code
        from interpreter import MylangeInterpreter
        parent:MylangeInterpreter = parent
        this.Parent:MylangeInterpreter = parent
        codeBlockLines:str = parent.CleanCodeCache[codeBody.strip()]
        lines = LanClass.clean_code_block(codeBlockLines)
        #print(lines)
        property_strs:list = [item for item in lines if ActualRegex.ProprotyStatement.value.search(item)]
        method_strs:list[re.Match[str]] = [ ActualRegex.FunctionStatement.value.match(item) for item in lines if ActualRegex.FunctionStatement.value.search(item)]
        operation_redeclaration_strs:list[re.Match[str]] = [ActualRegex.OperationRedeclaration.value.match(item) for item in lines if ActualRegex.OperationRedeclaration.value.search(item)]
        # Assign Proproties
        for proproty_init in property_strs:
            m = ActualRegex.ProprotyStatement.value.match(proproty_init)
            p_type = m.group(1)
            p_typeid = LanTypes.from_string(p_type)
            p_name = m.group(2)
            p_init = RandomTypeConversions.convert(m.group(3)) if (m.group(3)) else VariableValue(p_typeid, None)
            this.set_property(p_name, p_typeid, p_init)
        # Methods
        for method_init in (method_strs + operation_redeclaration_strs):
            init_param_str = ",".join(["set this"] + method_init.group(3).split(','))
            funct = LanFunction(m.group(2), method_init.group(1), init_param_str, parent.CleanCodeCache[method_init.group(4)])
            this.Methods[method_init.group(2)] =  funct
    
    def set_property(this, name:str, typeid:LanTypes, value:VariableValue):
        this.Properties[name] = value

    def create(this, args):
        this.do_method("constructor", args)
        return VariableValue(LanTypes.casting, copy.deepcopy(this))
    
    def props_to_set(this) -> VariableValue:
        return VariableValue(LanTypes.set, this.Properties)
    
    def do_method(this, method_name:str, args:list[VariableValue]) -> VariableValue:
        # Copy the Function
        ps = [this.props_to_set()] + args
        return this.Methods[method_name].execute(this.Parent, ps, False, this)
    
    def has_method(this, methodName:str) -> bool:
        return methodName in this.Methods.keys()


