# IMPORT
import re
import json
import copy

from lanregexes import ActualRegex
from memory import MemoryBooker
from lantypes import LanTypes, VariableValue, RandomTypeConversions, ParamChecker
#from booleanlogic import LanBooleanStatementLogic
from lanarithmetic import LanArithmetics
from builtinfunctions import MylangeBuiltinFunctions, VariableTypeMethods
from lanerrors import LanErrors
from interface import AnsiColor
from lanclass import LanClass, LanFunction
# GLOBALS
FILE_EXT:str = ".my"
NIL_RETURN:VariableValue = VariableValue(LanTypes.nil, None)
# Defines all the logic held by the different matches
def all_matchers(base):
    """Recursively yield all subclasses of `base`"""
    for subclass in base.__subclasses__():
        yield subclass
        yield from all_matchers(subclass)  # include nested subclasses

class LineMatcher:
    pattern: re.Pattern
    @classmethod
    def match(cls, this:'MylangeInterpreter', text: str):
        m = cls.pattern.search(text)
        if m:
            return cls.handle(this, m)
        return None
    @classmethod
    def handle(cls, this:'MylangeInterpreter', m:re.Match) -> VariableValue:
        """Override in subclasses"""
        raise NotImplementedError

class FormatMatcher:
    pattern: re.Pattern
    @classmethod
    def match(cls, text: str):
        m = cls.pattern.search(text)
        if m:
            return cls.handle(m)
        return None
    @classmethod
    def handle(cls, this:'MylangeInterpreter', m:re.Match) -> VariableValue:
        """Override in subclasses"""
        raise NotImplementedError

class MatchBox:
    # ============= #
    # Line Matchers #
    # ============= #
    class ReturnStatement(LineMatcher):
        pattern = ActualRegex.ReturnStatement.value
        @classmethod
        def handle(cls, this, m):
            r = this.format_parameter(m.group(1))
            this.echo(f"Returning a value: {r}", "re", 1)
            return r
    class ImportStatement(LineMatcher):
        pattern = ActualRegex.ImportStatement.value
        @classmethod
        def handle(cls, this, m):
            file_name:str = m.group(1) + FILE_EXT
            this.echo(f"Importing from {file_name}", "Importer")
            function_bloc:str = m.group(2)
            functions = [funct.strip() for funct in function_bloc.split(",")]
            # Setup Vitual envirement
            mi = MylangeInterpreter(f"Imports\\{m.group(1)}", startBlockCacheNumber=len([item for item in this.CleanCodeCache.keys() if item.startswith("0x")]))
            mi.make_child_block(this, False)
            with open(file_name, 'r') as imports_file:
                mi.interpret(imports_file.read())
                for funct_name in functions:
                    this.Booker.FunctionRegistry[funct_name] = mi.Booker.FunctionRegistry[funct_name]
                this.CleanCodeCache.update(mi.CleanCodeCache)
            return NIL_RETURN
    class VariableDecalaration(LineMatcher):
        pattern = ActualRegex.VariableDecleration.value
        @classmethod
        def handle(cls, this, m):
            typeid:int = LanTypes.from_string(m.group(2))
            name:str = m.group(3)
            value_str:str = m.group(5)
            value = this.format_parameter(value_str)
            this.echo(f"This is a Variable Declaration! {name}@{typeid}({m.group(2)}) {value}", indent=1)
            this.Booker.set(name, value)
            return NIL_RETURN
    class VariableRedeclaration(LineMatcher):
        pattern = ActualRegex.VariableRedeclaration.value
        @classmethod
        def handle(cls, this, m):
            varname:str = m.group(1)
            varextention:str = m.group(2)
            newvalue:str = m.group(3)
            #print(varname, varextention, newvalue)
            if not this.Booker.find(varname): raise LanErrors.MemoryMissingError()
            fullvarname:str = varname + (varextention if (varextention != None) else "")
            var = this.Booker.get(fullvarname)
            castedvalue = this.format_parameter(newvalue)
            if castedvalue.typeid != var.typeid: raise LanErrors.WrongTypeExpectationError()
            var.value = this.format_parameter(newvalue).value
            return NIL_RETURN
    class IfStatement(LineMatcher):
        pattern = ActualRegex.IfStatementGeneral.value
        @classmethod
        def handle(cls, this, m):
            #TODO: Refine this
            # Match to correct if/else block
            condition = None
            when_true = None 
            when_false = None
            if ActualRegex.IfElseStatement.value.search(m.group(0)):
                m = ActualRegex.IfElseStatement.value.match(m.group(0))
                condition = m.group(1)
                when_true = m.group(2)
                when_false = m.group(3)
            elif ActualRegex.IfStatement.value.search(m.group(0)):
                m = ActualRegex.IfStatement.value.match(m.group(0))
                condition = m.group(1)
                when_true = m.group(2)
            else:
                raise Exception("IF/Else statement not configured right!")
            this.echo(f"Parts: {when_true}, {when_false}, {condition}", indent=1)
            # Evaluate the statement
            result = (this.format_parameter(condition)).value
            if type(result) != bool:
                raise LanErrors.ConditionalNotBoolError(f"Cannot use this for boolean logic ({type(result)} {result}): {condition}")
            # Do functions
            if (result):
                block = MylangeInterpreter(f"{this.BlockTree}/IfTrue", this.LineNumber)
                block.make_child_block(this, True)
                block.interpret(when_true, True)
            elif (not result) and (when_false!=None):
                block = MylangeInterpreter(f"{this.BlockTree}/IfFalse", this.LineNumber)
                block.make_child_block(this, True)
                block.interpret(when_false, True)
            return NIL_RETURN
    class FunctionStatement(LineMatcher):
        pattern = ActualRegex.FunctionStatement.value
        @classmethod
        def handle(cls, this, m):
            return_type:str = m.group(1)
            function_name:str = m.group(2)
            function_parameters_string = m.group(3)
            function_code_string = m.group(4)
            funct = LanFunction(function_name, return_type, function_parameters_string, function_code_string)
            this.Booker.FunctionRegistry[function_name] = funct
            this.echo(f"Registered function by name: {function_name}")
            return NIL_RETURN
    class ClassDeclaration(LineMatcher):
        pattern = ActualRegex.ClassStatement.value 
        @classmethod
        def handle(cls, this, m):
            cls_name:str = m.group(1)
            cls_body:str = m.group(2)
            lan_cls = LanClass(cls_name, cls_body, this)
            this.Booker.ClassRegistry[cls_name] = lan_cls
            return NIL_RETURN
    class ForStatement(LineMatcher):
        pattern = ActualRegex.ForStatement.value
        @classmethod
        def handle(cls, this, m):
            loop_var_raw = str(m.group(1))
            loop_var=""
            unpack = False
            if loop_var_raw.startswith("[") and loop_var_raw.endswith("]"):
                unpack = True
                loop_var = loop_var_raw[1:-1]
            else:
                loop_var = loop_var_raw
            loop_over:VariableValue = this.format_parameter(m.group(2))
            ParamChecker.EnsureIntegrety((loop_over, LanTypes.array))
            loop_do_str:str = m.group(3)
            loop_funct = LanFunction("ForLoop", "nil", loop_var, loop_do_str)
            try:
                if unpack:
                    for item in loop_over.value: 
                        ParamChecker.EnsureIntegrety((item, LanTypes.array))
                        loop_funct.execute(this, item.value, True)
                else:
                    for item in loop_over.value: loop_funct.execute(this, [item], True)
            except LanErrors.Break: pass
            return NIL_RETURN
    class WhileStatement(LineMatcher):
        pattern = ActualRegex.WhileStatement.value
        @classmethod
        def handle(cls, this, m):
            while_condition = m.group(1).strip()
            while_do_str = m.group(2).strip()
            while_loop_funct = LanFunction("WhileLoop", "nil", "", while_do_str)
            try:
                while this.format_parameter(while_condition).value:
                    while_loop_funct.execute(this, [], True)
            except LanErrors.Break: pass
            return NIL_RETURN
    class MethodCall(LineMatcher):
        pattern = ActualRegex.FunctionOrMethodCall.value
        @classmethod
        def handle(cls, this, m):
            this.do_function_or_method(m.group(0))
            return NIL_RETURN
    class CachedBlock(LineMatcher):
        pattern = ActualRegex.CachedBlock.value
        @classmethod
        def handle(cls, this, m):
            r = this.interpret(this.CleanCodeCache[m.group(0).strip()], True)
            if (r != None): return r
    class BreakStatement(LineMatcher):
        pattern = ActualRegex.BreakStatement.value
        @classmethod
        def handle(cls, this, m):
            this.echo("Break Called")
            raise LanErrors.Break()
    
    # =============== #
    # Format Matchers #
    # =============== #



# Main Mylange Class
class MylangeInterpreter:
    Booker:MemoryBooker
    CleanCodeCache:dict[str,str]
    LambdaCache:dict[str, tuple[str, str, str]]
    BlockTree:str
    LineNumber:int
    StartBlockCacheNumber:int
    EchosEnables:bool = False

    def enable_echos(this) -> None:
        this.EchosEnables = True
    
    def echo(this, text:str, origin:str="MyIn", indent:int=0, anoyance:int=0) -> None:
        if not this.EchosEnables: return
        if (anoyance > 6): return
        indent += this.BlockTree.count('/')
        indentation:str = '\t'*indent
        print(f"{indentation}\033[36m[{this.LineNumber}:{origin}:{this.BlockTree}]\033[0m ", text)

    def __init__(this, blockTree:str, startingLineNumber:int=0, startBlockCacheNumber=0) -> None:
        #print("\033[33m<Creating Interpreter Class>\033[0m")
        this.Booker = MemoryBooker()
        this.CleanCodeCache = {}
        this.BlockTree = blockTree
        this.LineNumber = startingLineNumber
        this.StartBlockCacheNumber = startBlockCacheNumber

    def make_child_block(this, parent:'MylangeInterpreter', shareMemory:bool) -> None:
        # IF these are set dirrectly, then they will allow
        # the blocks to make changes to the master's data,
        # which may not be the funcionally wanted
        # if (booker != None): this.Booker = copy.deepcopy(booker)
        if (shareMemory): this.Booker = parent.Booker
        this.CleanCodeCache = copy.deepcopy(parent.CleanCodeCache)
        this.echo("Converting to Child Process")

    def interpret(this, string:str, overrideClean:bool=False, objectMethodMaster:LanClass=None) -> VariableValue:
        try:
            return this.interpret_logic(string, overrideClean, objectMethodMaster)
        except LanErrors.Break: raise LanErrors.Break()
        except LanErrors.MylangeError as exception:
            AnsiColor.println(f"Fatal Error: {exception.message}", AnsiColor.BRIGHT_RED)
            return None

    def interpret_logic(this, string:str, overrideClean:bool=False, objectMethodMaster:LanClass=None) -> VariableValue:
        lines:list[str] = this.make_chucks(string, overrideClean, this.StartBlockCacheNumber)
        Return:VariableValue = VariableValue(LanTypes.nil, None); macthed:bool = False
        for line in lines:
            this.echo(line, "MyInLoop")
            # Match the type of line
            for matcher in all_matchers(LineMatcher):
                result = matcher.match(this, line)
                if result is not None:
                    macthed = True
                    this.LineNumber += 1
                    if result.typeid != LanTypes.nil:
                        Return = result
                        break
            if not macthed: raise LanErrors.CannotFindQuerryError("Could not match this to anything?")
        return Return

    def make_chucks(this, string:str, overrideClean:bool=False, starBlockCacheNumber=0) -> list[str]:
        string:str = string
        for redecl in ActualRegex.Redefinitions.value.findall(string):
            redecl:str = redecl
            print("Found Redelaration: ", redecl)
            for item in redecl.strip().split(','):
                item_p = item.strip().split(" ")
                #LanRe.add_translation(item_p[0], item_p[1])
            string = string.replace(f"#!{redecl}", '')
        clean_code, clean_code_cache = CodeCleaner.cleanup_chunk(string, overrideClean, starBlockCacheNumber)
        this.CleanCodeCache.update(clean_code_cache)
        if (this.BlockTree == "Main") and this.EchosEnables:
            mem_blocks:list[str] = [f"{k} -> {v}" for k, v in this.CleanCodeCache.items()]
            joined_mem = '\n'.join(mem_blocks)
            AnsiColor.println(f"[Code Lines]\n{clean_code}\n[Memory Units]\n{joined_mem}", AnsiColor.BLUE)
        return [item for item in clean_code.split(";") if item != '']
    
    def format_parameter_list(this, string:str) -> list:
        commas_seperated:list[str] = CodeCleaner.split_top_level_commas(string)
        parts:list = []
        for part in commas_seperated:
            parts.append(this.format_parameter(part))
        return parts
    
    def format_parameter(this, part:str) -> VariableValue|LanFunction|None:
        part = part.strip()
        this.echo(f"Consitering: {part}", anoyance=2)
        Return = None
        if RandomTypeConversions.get_type(part)[0] != 0:
            this.echo("Casted to RandomType", anoyance=2)
            Return = RandomTypeConversions.convert(part, this)
        # Arithmetics #
        elif LanArithmetics.is_arithmetic(part):
            Return = LanArithmetics.evalute_string(this, part)
            this.echo(f"Casted to Arithmetic; returning {Return}", anoyance=2)
        # Function/Method Call #
        elif ActualRegex.FunctionOrMethodCall.value.search(part):
            this.echo("Casted to Function/Method", anoyance=2)
            Return = this.do_function_or_method(part)
        # Lambda #
        elif ActualRegex.LambdaStatement.value.search(part):
            m = ActualRegex.LambdaStatement.value.match(part)
            returnType = m.group(1)
            paramString = m.group(2)
            blockCache = this.CleanCodeCache[m.group(3)]
            this.echo("Casted to Lambda function")
            Return = LanFunction("lambda", returnType, paramString, blockCache)
        # New Object from Class #
        elif ActualRegex.NewClassObjectStatement.value.search(part):
            m = ActualRegex.NewClassObjectStatement.value.match(part)
            cls_name = m.group(1)
            cls_args = this.format_parameter_list(m.group(2))
            this.echo(f"Casted to New Class Object <{cls_name}>", anoyance=2)
            Return = this.Booker.ClassRegistry[cls_name].create(cls_args)
        # Cached #
        elif ActualRegex.CachedString.value.search(part):
            this.echo("Casted to Cached String", anoyance=2)
            Return = VariableValue(LanTypes.string, this.CleanCodeCache[part][1:-1])
        elif ActualRegex.CachedChar.value.search(part):
            this.echo("Casted to Cached Char", anoyance=2)
            Return = VariableValue(LanTypes.character, this.CleanCodeCache[part][1:-1])
        elif part.startswith("@") and ActualRegex.VariableStructure.value.search(part[1:]):
            ogvar = this.Booker.get(part[1:])
            Return = copy.deepcopy(ogvar)
        # Variable by Name #
        elif ActualRegex.VariableStructure.value.search(part) and (part not in this.SpecialValueWords):
            if this.Booker.find(part):
                r = this.Booker.get(part)
                this.echo(f"Casted to Variable: {r}", anoyance=2)
                Return = r
            # Function #
            elif part in this.Booker.FunctionRegistry.keys():
                this.echo("Casted to Function Name")
                Return = this.Booker.FunctionRegistry[part]
            else: raise LanErrors.MemoryMissingError(f"Cannot find variable by name: {part}")
        # Failsafe #
        else:
            this.echo("Casted to Failsafe RandomType Conversion", anoyance=2)
            Return = RandomTypeConversions.convert(part, this)
        
        if ((not isinstance(Return, VariableValue)) and (not isinstance(Return, LanFunction))):
            raise Exception("How am I not returning the right value? ", Return)
        else: 
            this.echo(f"Formating: Returning {Return}")
            return Return

    # Certain variable-name capatible words that should not
    # be ever treated like a variable.
    SpecialValueWords:list[str] = ["nil", "true", "false"]

    def get_method_aspects(_, string:str):
        if string.startswith("(") and string.endswith(")"):
            return (None, string[1:-1])
        m = re.match(r"^([\w\[\]:]+) *(?:\((.*)\))?$", string, re.UNICODE)
        return (m.group(1), m.group(2))

    def do_function_or_method(this, fromString:str) -> VariableValue:
        this.echo(F"Evaluating function: {fromString}", "doFu")
        # Before any workload, check if it is a Mylange Builtin Function
        builtinMatch = re.match(r"([\w.]+)\((.*)\)", fromString)
        if (builtinMatch != None) and (MylangeBuiltinFunctions.get_method(builtinMatch.group(1).split(".")) != None):
            this.echo("Found BUILTIN")
            f = MylangeBuiltinFunctions.get_method(builtinMatch.group(1).split("."))
            return f(this.Booker, *this.format_parameter_list(builtinMatch.group(2)))
        # First, break into method chain
        method_chain:list[tuple[str,str]] = [this.get_method_aspects(i) for i in CodeCleaner.split_top_level_commas(fromString.strip(), '.')]
        working_var:VariableValue = None
        for i, chain_link in enumerate(method_chain):
            #print(chain_link, working_var, type(working_var))
            if chain_link[0] == None:
                working_var = this.format_parameter(chain_link[1])
            else:
                formatedParams = this.format_parameter_list(chain_link[1]) if chain_link[1] != None else []
                working_var = this.evalute_method(working_var, chain_link[0], formatedParams, i)
        return working_var
        
    def evalute_method(this, base:VariableValue, methodName:str, methodParameters:list[VariableValue], chainIndex:int) -> VariableValue|LanFunction|None:
        # Create Virtual Workspace
        Return:VariableValue|LanFunction|None = None
        this.echo(f"Working chain -{chainIndex}-: {methodName}")
        if (RandomTypeConversions.convert(methodName, this).typeid != LanTypes.nil) and chainIndex == 0:
            # A Random Type Instance, at the base
            Return = RandomTypeConversions.convert(methodName, this)
        
        elif (MylangeBuiltinFunctions.is_builtin(methodName)) and chainIndex == 0:
            # Mylange base function
            Return = MylangeBuiltinFunctions.fire_builtin(this.Booker, methodName, methodParameters)
        elif isinstance(base, VariableValue) and (VariableTypeMethods.is_applitable(base.typeid, methodName)):
            # Mylange type base method
            Return = VariableTypeMethods.fire_variable_method(this, methodName, base, methodParameters)
        elif (methodName in this.Booker.FunctionRegistry.keys()) and chainIndex == 0:
            # User-defined function
            Return = this.Booker.FunctionRegistry[methodName].execute(this, methodParameters)
        elif (methodName in this.Booker.ClassRegistry.keys()) and chainIndex == 0:
            #TODO: User-defined static method
            raise NotImplementedError()
        elif (this.get_cached_reference(methodName) != None) and chainIndex == 0:
            # A Random Type Instance, but cached
            Return = VariableValue(LanTypes.string, this.get_cached_reference(methodName))
        elif (this.Booker.find(methodName)) and chainIndex == 0:
            # Variable, most likely as a chain base
            Return = this.Booker.get(methodName)
        else: raise Exception(f"Cannot find Function/Method/Class/Variable for method: {methodName}")
        return Return
    
    def get_cached_reference(this, hexCode:str) -> str|None:
        if hexCode in this.CleanCodeCache.keys():
            return this.CleanCodeCache[hexCode][1:-1]
        return None

# Pre-processes code into interpreter-efficient executions
class CodeCleaner:
    "Converts a string of Mylange code into a execution-ready code blob."
    
    @staticmethod
    def cleanup_chunk(string:str, preventConfine:bool=False, startBlockNumber:int=0):
        clean_code:str = CodeCleaner.remove_comments(string)
        cache:dict[str,str] = {}
        if not preventConfine:
            # first, take care of string/char values
            clean_code, qoute_cache = CodeCleaner.confine_qoutes(clean_code)
            cache.update(qoute_cache)
            # then, confine all of the lambda instances

            # then, remove all blocks
            clean_code, block_cache = CodeCleaner.confine_brackets(clean_code, startBlockNumber=startBlockNumber)
            cache.update(block_cache)
        clean_code = clean_code.replace('\n', '')
        return clean_code, cache
    
    @staticmethod
    def remove_comments(string:str) -> str:
        result:str = re.sub(r"^//.*$", '', string, flags=re.MULTILINE)
        result = re.sub(r"/\[[\w\W]*\]/", '', result, flags=re.MULTILINE)
        return result

    # thanks ChatGPT
    @staticmethod
    def confine_brackets(s, index_tracker=None, block_dict=None, startBlockNumber=0):
        if index_tracker is None:
            index_tracker = {'index': startBlockNumber}
        if block_dict is None:
            block_dict = {}

        result = []
        i = 0
        last_index = 0
        stack = []

        while i < len(s):
            if s[i] == '{':
                if not stack:
                    start = i
                stack.append(i)
            elif s[i] == '}':
                if stack:
                    stack.pop()
                    if not stack:
                        end = i + 1
                        inner_block = s[start:end]
                        # Recursively replace inside this block (excluding outer braces)
                        inner_content = inner_block[1:-1]
                        replaced_inner, block_dict = CodeCleaner.confine_brackets(
                            inner_content, index_tracker, block_dict
                        )
                        # Reconstruct cleaned block and store it
                        #cleaned_block = '{' + replaced_inner + '}'

                        # remove all return lines, begining spaces, extra spaces, etc.
                        cleaned_block = re.sub(r"^ +", '', replaced_inner, flags=re.MULTILINE)
                        cleaned_block = re.sub(r"\n", '', cleaned_block, flags=re.MULTILINE)
                        cleaned_block = re.sub(r" +", ' ', cleaned_block, flags=re.MULTILINE)

                        hex_key = f"0x{index_tracker['index']:X}"
                        index_tracker['index'] += 1
                        block_dict[hex_key] = cleaned_block
                        result.append(s[last_index:start])
                        result.append(hex_key)
                        last_index = end
            i += 1

        result.append(s[last_index:])
        return ''.join(result), block_dict
    
    @staticmethod
    def confine_qoutes(s:str):
        i = 0
        result = []
        last_index = 0
        blocks = {}
        single_index = 0
        double_index = 0

        while i < len(s):
            if s[i] in {"'", '"'}:
                quote_char = s[i]
                start = i
                i += 1
                escaped = False
                while i < len(s):
                    if s[i] == '\\' and not escaped:
                        escaped = True
                    elif s[i] == quote_char and not escaped:
                        break
                    else:
                        escaped = False
                    i += 1
                if i < len(s) and s[i] == quote_char:
                    end = i + 1
                    block = s[start:end]
                    if quote_char == "'":
                        key = f"1x{single_index:X}"
                        single_index += 1
                    else:
                        key = f"2x{double_index:X}"
                        double_index += 1
                    blocks[key] = block
                    result.append(s[last_index:start])
                    result.append(key)
                    last_index = end
            i += 1

        result.append(s[last_index:])
        return ''.join(result), blocks
    
    BlockBeginngings = ['(', '[', '{']
    BlockEndings = [')', ']', '}']

    @staticmethod
    def split_top_level_commas(s, comma=',') -> list[str]:
        result = []
        depth = 0
        current = []

        for char in s:
            if char == comma and depth == 0:
                result.append(''.join(current))
                current = []
            else:
                if char in CodeCleaner.BlockBeginngings:
                    depth += 1
                elif char in CodeCleaner.BlockEndings:
                    depth -= 1
                current.append(char)

        if current:
            result.append(''.join(current))

        return result

# Custom JSON Encoder
class MylangeClassEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, VariableValue):
            return {"typeid": obj.typeid, "value": obj.value}
        return json.JSONEncoder.default(self, obj)