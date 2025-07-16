# IMPORTS
import re
import copy

from lantypes import LanTypes, VariableValue, RandomTypeConversions
from lanerrors import LanErrors
from lanregexes import LanRe
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
    
    def execute(this, parent:any, params:list[VariableValue], includeMemory:bool=False, objectMethodMaster:'LanClass'=None) -> any:
        from interpreter import MylangeInterpreter
        parent:MylangeInterpreter = parent
        container = MylangeInterpreter(f"Funct\\{this.Name}")
        if parent.EchosEnables: container.enable_echos()
        old_mem_keys:list[str] = []
        mem = None
        if includeMemory:
            mem = parent.Booker
            old_mem_keys = list(parent.Booker.Registry.keys())
        container.make_child_block(parent, False)
        # Add parameters
        if len(params) != len(this.Parameters):
            raise Exception(f"Length of Given and Expected Parameters do not Match: given {len(params)}, expected {len(this.Parameters)}")
        for i, param in enumerate(this.Parameters.items()):
            if params[i].typeid != param[1]: raise Exception("Parameter given and expected do not match types!")
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
        r = re.sub(r"\n", '', codeBody, flags=re.MULTILINE)
        r = re.sub(r"^ +", '', r, flags=re.MULTILINE)
        r = re.sub(r" +", ' ', r, flags=re.MULTILINE)
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
        property_strs:list = [item for item in lines if re.search(LanRe.ProprotyStatement, item, re.MULTILINE)]
        method_strs:list = [item for item in lines if re.search(LanRe.FunctionStatement, item)]
        # Assign Proproties
        for proproty_init in property_strs:
            m = re.search(LanRe.ProprotyStatement, proproty_init)
            p_type = m.group(1)
            p_name = m.group(2)
            p_init = RandomTypeConversions.convert(m.group(3)) if (m.group(3)) else None
            this.set_property(p_name, LanTypes.from_string(p_type), p_init)
        for method_init in method_strs:
            m = re.search(LanRe.FunctionStatement, method_init)
            init_param_str = ",".join(["set this"] + m.group(3).split(','))
            funct = LanFunction(m.group(2), m.group(1), init_param_str, parent.CleanCodeCache[m.group(4)])
            this.Methods[m.group(2)] =  funct
    
    def set_property(this, name:str, typeid:LanTypes, value:VariableValue):
        this.Properties[name] = value

    def create(this, args):
        this.do_method("constructor", args)
        return VariableValue(-1, copy.deepcopy(this))
    
    def props_to_set(this) -> VariableValue:
        return VariableValue(LanTypes.set, this.Properties)
    
    def do_method(this, method_name:str, args:list[VariableValue]) -> VariableValue:
        # Copy the Function
        ps = [this.props_to_set()] + args
        return this.Methods[method_name].execute(this.Parent, ps, False, this)


