# IMPORT
import re
import json
import copy

from lanregexes import ActualRegex
from memory import MemoryBooker
from lantypes import VariableValue, RandomTypeConversions, ParamChecker, LanType, LanScaffold
#from booleanlogic import LanBooleanStatementLogic
from lanarithmetic import LanArithmetics
from builtinfunctions import MylangeBuiltinFunctions, VariableTypeMethods
from lanerrors import LanErrors
from interface import AnsiColor
from lanclass import LanClass, LanFunction
# GLOBALS
FILE_EXT:str = ".my"
NIL_RETURN:VariableValue = VariableValue(LanType.nil(), None)
# Defines all the logic held by the different matches
def all_matchers(base):
    """Recursively yield all subclasses of `base`"""
    for subclass in base.__subclasses__():
        yield subclass
        yield from all_matchers(subclass)  # include nested subclasses

class LineMatcher:
    pattern: re.Pattern
    @classmethod
    def match(cls, self:'MylangeInterpreter', text: str):
        m = cls.pattern.search(text)
        if m:
            return cls.handle(self, m)
        return None
    @classmethod
    def handle(cls, self:'MylangeInterpreter', m:re.Match) -> VariableValue|LanFunction|None:
        """Override in subclasses"""
        raise NotImplementedError

class MatchBox:
    # ============= #
    # Line Matchers #
    # ============= #
    class ReturnStatement(LineMatcher):
        pattern = ActualRegex.ReturnStatement.value
        @classmethod
        def handle(cls, self, m):
            r = self.format_parameter(m.group(1))
            self.echo(f"Returning a value: {r}", "re", 1)
            return r
    class ImportStatement(LineMatcher):
        pattern = ActualRegex.ImportStatement.value
        @classmethod
        def handle(cls, self, m):
            file_name:str = m.group(1) + FILE_EXT
            self.echo(f"Importing from {file_name}", "Importer")
            function_bloc:str = m.group(2)
            functions = [funct.strip() for funct in function_bloc.split(",")]
            # Setup Vitual envirement
            mi = MylangeInterpreter(f"Imports\\{m.group(1)}", startBlockCacheNumber=len([item for item in self.CleanCodeCache.keys() if item.startswith("0x")]))
            mi.make_child_block(self, False)
            with open(file_name, 'r') as imports_file:
                mi.interpret(imports_file.read())
                for funct_name in functions:
                    self.echo(f"Processing import request: {funct_name}")
                    if (funct_name in mi.Booker.FunctionRegistry):
                        self.Booker.FunctionRegistry[funct_name] = mi.Booker.FunctionRegistry[funct_name]
                    elif (funct_name in mi.Booker.ClassRegistry):
                        self.Booker.ClassRegistry[funct_name] = mi.Booker.ClassRegistry[funct_name]
                    else: raise LanErrors.MissingImportError()
                self.CleanCodeCache.update(mi.CleanCodeCache)
            return NIL_RETURN
    class VariableDecalaration(LineMatcher):
        pattern = ActualRegex.VariableDecleration.value
        @classmethod
        def handle(cls, self, m):
            typeid = LanType.get_type_from_typestr(m.group(1))
            name:str = m.group(2)
            value_str:str = m.group(4)
            value = self.format_parameter(value_str)
            # Ensure that the variable and what it's being assinged match in type
            if (type(value) is VariableValue) and typeid != value.Type:
                if typeid == LanScaffold.array and value.Type == LanScaffold.array:
                    if value.value == []: pass
                    elif typeid.Archetype is None: pass
                elif typeid == LanScaffold.set and value.Type == LanScaffold.set:
                    if value.value == {}: pass
                    elif typeid.Archetype is None: pass
                else: raise LanErrors.WrongTypeExpectationError(f"The type declared and recieved do not match! Expected {typeid}, got {value.Type}")
            self.echo(f"self is a Variable Declaration! {name}@{typeid}({m.group(2)}) {value}", indent=1)
            assert type(value) is VariableValue
            # Create the real, correctly typed varibale, as some empty arrays/sets will remove their archetypes
            var = VariableValue(typeid, value.value)
            self.Booker.set(name, var)
            return NIL_RETURN
    class VariableRedeclaration(LineMatcher):
        pattern = ActualRegex.VariableRedeclaration.value
        @classmethod
        def handle(cls, self, m):
            varname:str = m.group(1)
            varextention:str = m.group(2)
            newvalue:str = m.group(3)
            #print(varname, varextention, newvalue)
            if not self.Booker.find(varname): raise LanErrors.MemoryMissingError()
            fullvarname:str = varname + (varextention if (varextention != None) else "")
            var = self.Booker.get(fullvarname)
            castedvalue = self.format_parameter(newvalue)
            assert type(castedvalue) is VariableValue
            if castedvalue.Type != var.Type: raise LanErrors.WrongTypeExpectationError()
            form = self.format_parameter(newvalue); assert type(form) is VariableValue
            var.value = form.value
            return NIL_RETURN
    class IfStatement(LineMatcher):
        pattern = ActualRegex.IfStatementBlock.value
        @classmethod
        def handle(cls, self, m):
            self.echo(f"[DEBRA] If Statement: {m.group(0)}")
            ms = re.findall(ActualRegex.IfStatementParts.value, m.group(0))
            # 1 = if/else if/else
            # 2 = boolean evaluation (opitonal)
            # 3 = logic
            for m in ms:
                if_type:str = re.sub(r"\s*", "", m[0]); bool_test:str = m[1]; logic:str = m[2]
                proceed:bool = False
                if (if_type == "else"):
                    proceed = True
                else:
                    bool_res = self.format_parameter(bool_test); assert type(bool_res) is VariableValue
                    ParamChecker.EnsureIntegrety((bool_res, LanType.bool()))
                    assert type(bool_res.value) is bool
                    proceed = bool_res.value
                if proceed:
                    funct = LanFunction("If", LanType.nil(), {}, logic)
                    funct.execute(self, [], True)
                    break
            return NIL_RETURN
    class FunctionStatement(LineMatcher):
        pattern = ActualRegex.FunctionStatement.value
        @classmethod
        def handle(cls, self, m):
            return_type = LanType.get_type_from_typestr(m.group(1))
            function_name:str = m.group(2)
            function_parameters_string = m.group(3)
            function_code_string = m.group(4)
            funct = LanFunction(function_name, return_type, function_parameters_string, function_code_string)
            self.Booker.FunctionRegistry[function_name] = funct
            self.echo(f"Registered function by name: {function_name}")
            return NIL_RETURN
    class ClassDeclaration(LineMatcher):
        pattern = ActualRegex.ClassStatement.value 
        @classmethod
        def handle(cls, self, m):
            cls_name:str = m.group(1)
            cls_body:str = m.group(2)
            lan_cls = LanClass(cls_name, cls_body, self)
            self.Booker.ClassRegistry[cls_name] = lan_cls
            return NIL_RETURN
    class ForStatement(LineMatcher):
        pattern = ActualRegex.ForStatement.value
        @classmethod
        def handle(cls, self, m:re.Match[str]):
            loop_var_raw = m.group(1); assert m is not None
            loop_var=""
            unpack = False
            if loop_var_raw.startswith("[") and loop_var_raw.endswith("]"):
                unpack = True
                loop_var = loop_var_raw[1:-1]
            else:
                loop_var = loop_var_raw
            loop_over = self.format_parameter(m.group(2))
            assert type(loop_over) is VariableValue
            ParamChecker.EnsureIntegrety((loop_over, LanType(LanScaffold.array)))
            loop_do_str:str = m.group(3)
            loop_var_dict:dict[str,LanType] = {}
            loop_funct = LanFunction("ForLoop", LanType.nil(), LanType.make_param_type_dict(loop_var), loop_do_str)
            assert type(loop_over.value) is list
            if unpack:
                for item in loop_over.value: 
                    ParamChecker.EnsureIntegrety((item, LanType(LanScaffold.array)))
                    assert type(item.value) is list[VariableValue]
                    _ = loop_funct.execute(self, item.value, True)
            else:
                for item in loop_over.value: loop_funct.execute(self, [item], True)
            self.echo("For loop closed")
            return NIL_RETURN
    class WhileStatement(LineMatcher):
        pattern = ActualRegex.WhileStatement.value
        @classmethod
        def handle(cls, self, m):
            while_condition = m.group(1).strip()
            while_do_str = m.group(2).strip()
            while_loop_funct = LanFunction("WhileLoop", LanType.nil(), {}, while_do_str)
            vparam = self.format_parameter(while_condition); assert type(vparam) is VariableValue
            while vparam.value:
                try:
                    while_loop_funct.execute(self, [], True)
                except LanErrors.Break: break
                except LanErrors.Continue: continue
            return NIL_RETURN
    class MethodCall(LineMatcher):
        pattern = ActualRegex.FunctionOrMethodCall.value
        @classmethod
        def handle(cls, self, m):
            self.do_function_or_method(m.group(0))
            return NIL_RETURN
    class CachedBlock(LineMatcher):
        pattern = ActualRegex.CachedBlock.value
        @classmethod
        def handle(cls, self, m):
            r = self.interpret(self.CleanCodeCache[m.group(0).strip()], True)
            if (r != None): return r
    class BreakStatement(LineMatcher):
        pattern = ActualRegex.BreakStatement.value
        @classmethod
        def handle(cls, self, m):
            self.echo("Break Called")
            raise LanErrors.Break()

# Main Mylange Class
class MylangeInterpreter:
    Booker:MemoryBooker
    CleanCodeCache:dict[str,str]
    LambdaCache:dict[str, tuple[str, str, str]]
    BlockTree:str
    LineNumber:int
    StartBlockCacheNumber:int
    EchosEnables:bool = False

    def enable_echos(self) -> None:
        self.EchosEnables = True
    
    def echo(self, text:str, origin:str="MyIn", indent:int=0, anoyance:int=0) -> None:
        if not self.EchosEnables: return
        if (anoyance > 6): return
        indent += self.BlockTree.count('/')
        indentation:str = '\t'*indent
        print(f"{indentation}\033[36m[{self.LineNumber}:{origin}:{self.BlockTree}]\033[0m ", text)

    def __init__(self, blockTree:str, startingLineNumber:int=0, startBlockCacheNumber=0) -> None:
        #print("\033[33m<Creating Interpreter Class>\033[0m")
        self.Booker = MemoryBooker()
        self.CleanCodeCache = {}
        self.BlockTree = blockTree
        self.LineNumber = startingLineNumber
        self.StartBlockCacheNumber = startBlockCacheNumber

    def make_child_block(self, parent:'MylangeInterpreter', shareMemory:bool) -> None:
        # IF these are set dirrectly, then they will allow
        # the blocks to make changes to the master's data,
        # which may not be the funcionally wanted
        # if (booker != None): self.Booker = copy.deepcopy(booker)
        if (shareMemory): self.Booker = parent.Booker
        self.CleanCodeCache = copy.deepcopy(parent.CleanCodeCache)
        self.echo("Converting to Child Process")

    ObjectMethodMaster:LanClass|None

    def interpret(self, string:str, overrideClean:bool=False, objectMethodMaster:LanClass|None=None) -> VariableValue|None:
        self.ObjectMethodMaster = objectMethodMaster
        try:
            return self.interpret_logic(string, overrideClean)
        except LanErrors.Break: 
            raise LanErrors.Break()
        except LanErrors.MylangeError as exception:
            print(f"Fatal Error: {exception}"*AnsiColor.BRIGHT_RED)
            return None

    def interpret_logic(self, string:str, overrideClean:bool=False) -> VariableValue:
        lines:list[str] = self.make_chucks(string, overrideClean, self.StartBlockCacheNumber)
        Return:VariableValue = VariableValue(LanType.nil(), None); matched:bool = False
        for line in lines:
            self.echo(line, "MyInLoop")
            # Match the type of line
            for matcher in all_matchers(LineMatcher):
                result = matcher.match(self, line)
                if type(result) is VariableValue:
                    matched = True
                    self.LineNumber += 1
                    if (result.Type != LanScaffold.nil):
                        Return = result
                        break
                    elif matched:
                        break
            if not matched: raise LanErrors.CannotFindQuerryError(f"Could not match self to anything: {line}")
        return Return

    def make_chucks(self, string:str, overrideClean:bool=False, starBlockCacheNumber=0) -> list[str]:
        for redecl in ActualRegex.Redefinitions.value.findall(string):
            redecl:str = redecl
            print("Found Redelaration: ", redecl)
            for item in redecl.strip().split(','):
                item_p = item.strip().split(" ")
                #LanRe.add_translation(item_p[0], item_p[1])
            string = string.replace(f"#!{redecl}", '')
        clean_code, clean_code_cache = CodeCleaner.cleanup_chunk(string, overrideClean, starBlockCacheNumber)
        self.CleanCodeCache.update(clean_code_cache)
        if (self.BlockTree == "Main") and self.EchosEnables:
            mem_blocks:list[str] = [f"{k} -> {v}" for k, v in self.CleanCodeCache.items()]
            joined_mem = '\n'.join(mem_blocks)
            print(f"[Code Lines]\n{clean_code}\n[Memory Units]\n{joined_mem}"*AnsiColor.BLUE)
        return [item for item in clean_code.split(";") if item != '']
    
    def format_parameter_list(self, string:str) -> list:
        commas_seperated:list[str] = CodeCleaner.split_top_level_commas(string)
        parts:list = []
        for part in commas_seperated:
            parts.append(self.format_parameter(part))
        return parts
    
    def format_parameter(self, part:str) -> VariableValue|LanFunction|None:
        part = part.strip()
        self.echo(f"Consitering: {part}", anoyance=2)
        Return = None
        if RandomTypeConversions.get_type(part)[0] != 0:
            self.echo("Casted to RandomType", anoyance=2)
            Return = RandomTypeConversions.convert(part, self)
        # Function/Method Call #
        elif ActualRegex.FunctionOrMethodCall.value.search(part):
            self.echo("Casted to Function/Method", anoyance=2)
            Return = self.do_function_or_method(part)
        # Arithmetics #
        elif LanArithmetics.is_arithmetic(part):
            self.echo("Thinking of Arithmetics")
            Return = LanArithmetics.evalute_string(self, part)
            self.echo(f"Casted to Arithmetic; returning {Return}", anoyance=2)
        # Lambda #
        elif ActualRegex.LambdaStatement.value.search(part):
            m = ActualRegex.LambdaStatement.value.match(part); assert m is not None
            returnType = LanType.get_type_from_typestr(m.group(1))
            paramDict = LanType.make_param_type_dict(m.group(2))
            blockCache = self.CleanCodeCache[m.group(3)]
            self.echo("Casted to Lambda function")
            Return = LanFunction("lambda", returnType, paramDict, blockCache)
        # New Object from Class #
        elif ActualRegex.NewClassObjectStatement.value.search(part):
            self.echo("Thinking of New Class Object")
            m = ActualRegex.NewClassObjectStatement.value.match(part); assert m is not None
            cls_name = m.group(1)
            cls_args = self.format_parameter_list(m.group(2))
            self.echo(f"Casted to New Class Object <{cls_name}>", anoyance=2)
            Return = self.Booker.ClassRegistry[cls_name].create(cls_args)
        # Cached #
        elif ActualRegex.CachedString.value.search(part):
            self.echo("Casted to Cached String", anoyance=2)
            Return = VariableValue(LanType.string(), self.CleanCodeCache[part][1:-1])
        elif ActualRegex.CachedChar.value.search(part):
            self.echo("Casted to Cached Char", anoyance=2)
            Return = VariableValue(LanType.char(), self.CleanCodeCache[part][1:-1])
        elif part.startswith("@") and ActualRegex.VariableStructure.value.search(part[1:]):
            self.echo("Casted to Copytrace of variable.")
            ogvar = self.Booker.get(part[1:])
            Return = copy.deepcopy(ogvar)
        # Variable by Name #
        elif ActualRegex.VariableStructure.value.search(part) and (part not in self.SpecialValueWords):
            if self.Booker.find(part):
                r = self.Booker.get(part)
                self.echo(f"Casted to Variable: {r}", anoyance=2)
                Return = r
            # Function #
            elif part in self.Booker.FunctionRegistry.keys():
                self.echo("Casted to Function Name")
                Return = self.Booker.FunctionRegistry[part]
            else: raise LanErrors.MemoryMissingError(f"Cannot find variable by name: {part}")
        # Failsafe #
        else:
            self.echo("Casted to Failsafe RandomType Conversion", anoyance=2)
            Return = RandomTypeConversions.convert(part, self)
        
        if ((not isinstance(Return, VariableValue)) and (not isinstance(Return, LanFunction))):
            raise Exception("How am I not returning the right value? ", Return)
        else: 
            self.echo(f"Formating: Returning {Return}")
            return Return

    # Certain variable-name capatible words that should not
    # be ever treated like a variable.
    SpecialValueWords:list[str] = ["nil", "true", "false", "self"]

    def get_method_aspects(self, string:str):
        if string.startswith("(") and string.endswith(")"):
            return (None, string[1:-1])
        m = re.match(r"^([\w\[\]:]+) *(?:\((.*)\))?$", string, re.UNICODE); assert m is not None
        return (m.group(1), m.group(2))

    def do_function_or_method(self, fromString:str) -> VariableValue:
        self.echo(F"Evaluating function: {fromString}", "doFu")
        # Before any workload, check if it is a Mylange Builtin Function
        builtinMatch = re.match(r"([\w.]+)\((.*)\)", fromString)
        if (builtinMatch != None) and (MylangeBuiltinFunctions.get_method(builtinMatch.group(1).split(".")) != None):
            self.echo("Found BUILTIN")
            f = MylangeBuiltinFunctions.get_method(builtinMatch.group(1).split("."))
            assert f is not None
            return f(self.Booker, *self.format_parameter_list(builtinMatch.group(2)))
        # First, break into method chain
        method_chain:list[tuple[str|None,str]] = [self.get_method_aspects(i) for i in CodeCleaner.split_top_level_commas(fromString.strip(), '.')]
        working_var:VariableValue|LanFunction|None = None
        for i, chain_link in enumerate(method_chain):
            #print(chain_link, working_var, type(working_var))
            if chain_link[0] is None:
                working_var = self.format_parameter(chain_link[1])
            else:
                formatedParams = self.format_parameter_list(chain_link[1]) if chain_link[1] != None else []
                if (working_var is not None) and (type(working_var) is not VariableValue): raise LanErrors.MylangeError(f"Expected Variable value, got {type(working_var)} for '{working_var}'")
                working_var = self.evalute_method(working_var, chain_link[0], formatedParams, i)
        assert type(working_var) is VariableValue
        return working_var
        
    def evalute_method(self, base:VariableValue|None, methodName:str, methodParameters:list[VariableValue], chainIndex:int) -> VariableValue|LanFunction|None:
        # Create Virtual Workspace
        Return:VariableValue|LanFunction|None = None
        self.echo(f"Working chain -{chainIndex}-: {methodName}; {methodParameters}")
        if (base != None) and (base.Type == LanScaffold.casting):
            self.echo("Accessing Casting method")
            b = base.value; assert type(b) is LanClass
            Return = b.do_method(methodName, methodParameters)
        elif (RandomTypeConversions.convert(methodName, self).Type != LanScaffold.nil) and chainIndex == 0:
            # A Random Type Instance, at the base
            Return = RandomTypeConversions.convert(methodName, self)
        elif (MylangeBuiltinFunctions.is_builtin([methodName])) and chainIndex == 0:
            # Mylange base function
            f = MylangeBuiltinFunctions.get_method([methodName]); assert f is not None
            Return = f(self.Booker, methodParameters)
        elif isinstance(base, VariableValue) and (VariableTypeMethods.is_applitable(base.Type.TypeNum, methodName)):
            # Mylange type base method
            Return = VariableTypeMethods.fire_variable_method(self, methodName, base, methodParameters)
        elif (methodName in self.Booker.FunctionRegistry.keys()) and chainIndex == 0:
            # User-defined function
            Return = self.Booker.FunctionRegistry[methodName].execute(self, methodParameters)
        elif (methodName in self.Booker.ClassRegistry.keys()) and chainIndex == 0:
            #TODO: User-defined static method
            raise NotImplementedError()
        elif (self.get_cached_reference(methodName) != None) and chainIndex == 0:
            # A Random Type Instance, but cached
            Return = VariableValue(LanType.string(), self.get_cached_reference(methodName))
        elif (self.Booker.find(methodName)) and chainIndex == 0:
            # Variable, most likely as a chain base
            Return = self.Booker.get(methodName)
        else: raise Exception(f"Cannot find Function/Method/Class/Variable for method: {methodName}")
        self.echo(f"Returning: {Return}")
        return Return
    
    def get_cached_reference(self, hexCode:str) -> str|None:
        if hexCode in self.CleanCodeCache.keys():
            return self.CleanCodeCache[hexCode][1:-1]
        return None

# Pre-processes code into interpreter-efficient executions
class CodeCleaner:
    "Converts a string of Mylange code into a execution-ready code blob."
    
    @classmethod
    def cleanup_chunk(cls, string:str, preventConfine:bool=False, startBlockNumber:int=0):
        clean_code:str = cls.remove_comments(string)
        cache:dict[str,str] = {}
        if not preventConfine:
            # first, take care of string/char values
            clean_code, qoute_cache = cls.confine_qoutes(clean_code)
            cache.update(qoute_cache)
            # then, confine all of the lambda instances

            # then, remove all blocks
            clean_code, block_cache = cls.confine_brackets(clean_code, startBlockNumber=startBlockNumber)
            cache.update(block_cache)
        clean_code = clean_code.replace('\n', '')
        return clean_code, cache
    
    @staticmethod
    def remove_comments(string:str) -> str:
        result:str = re.sub(r"^//.*$", '', string, flags=re.MULTILINE)
        result = re.sub(r"\/\[[\w\W]*?\]\/", '', result, flags=re.MULTILINE)
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
        start:int|None = None
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
                        # Recursively replace inside self block (excluding outer braces)
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
    def split_top_level_commas(s, comma=',', additionalBrackets:list[tuple[str,str]]=[]) -> list[str]:
        result = []
        depth = 0
        current = []

        for char in s:
            if char == comma and depth == 0:
                result.append(''.join(current))
                current = []
            else:
                if char in CodeCleaner.BlockBeginngings + [a[0] for a in additionalBrackets]:
                    depth += 1
                elif char in CodeCleaner.BlockEndings + [a[1] for a in additionalBrackets]:
                    depth -= 1
                current.append(char)

        if current:
            result.append(''.join(current))

        return result

# Custom JSON Encoder
class MylangeClassEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, VariableValue):
            return {"typeid": str(o.Type), "value": o.value}
        return json.JSONEncoder.default(self, o)