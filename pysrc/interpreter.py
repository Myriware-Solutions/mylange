# IMPORT
import re, json, copy, os
from enum import IntFlag

from lanregexes import ActualRegex
from memory import MemoryBooker
from lantypes import VariableValue, RandomTypeConversions, ParamChecker, LanType, LanScaffold
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
            prefix = os.path.dirname(self.FilePath) + "/" if self.FilePath else "./"
            file_path:str = prefix + m.group(1)
            if not re.match(rf"{FILE_EXT}$", file_path): file_path += FILE_EXT
            file_path = re.sub(r"/+", "/", file_path.replace("\\", "/"))
            self.echo(f"Importing from {file_path}", "Importer")
            classes_block:str = m.group(2)
            classes = [funct.strip() for funct in classes_block.split(",")]
            # Setup Vitual envirement
            mil = MylangeInterpreter(f"Imports\\{m.group(1)}")
            if self.EchosEnables: mil.enable_echos()
            try:
                with open(file_path, 'r') as imports_file:
                    mil.interpret(imports_file.read())
                    for class_name in classes:
                        self.echo(f"Processing import request: {class_name}")
                        if class_name in mil.Booker._class_registry.keys():
                            class_obj = mil.Booker.GetClass(class_name)
                            class_obj.Import = True
                            self.Booker.SetClass(class_name, class_obj)
                        else: raise LanErrors.MissingImportError()
            except FileNotFoundError:
                raise LanErrors.MissingImportFileError(file_path)
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
            if not self.Booker.find(varname): raise LanErrors.MemoryMissingError(varname)
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
            function_name = m.group(2); assert type(function_name) is str
            function_parameters_string = m.group(3)
            function_parameters = LanType.make_param_type_dict(function_parameters_string)
            function_code_string = m.group(4)
            funct = LanFunction(function_name, return_type, function_parameters, function_code_string)
            
            f_id = self.Booker.SetFunction(function_name, funct)
            
            self.echo(f"Registered function by name: {function_name}, {f_id}")
            return NIL_RETURN
    class ClassDeclaration(LineMatcher):
        pattern = ActualRegex.ClassStatement.value 
        @classmethod
        def handle(cls, self, m):
            cls_name:str = m.group(1)
            cls_body:str = m.group(2)
            lan_cls = LanClass(cls_name, cls_body, self)
            self.Booker.SetClass(cls_name, lan_cls)
            return NIL_RETURN
    class TryCatchStatement(LineMatcher):
        pattern = ActualRegex.TryCatchStatement.value
        @classmethod
        def handle(cls, self:'MylangeInterpreter', m: re.Match) -> VariableValue | LanFunction | None:
            safe_block = m.group(1)
            exceptions_blocks_ms = [ActualRegex.ExceptionAsByStatement.value.match(item.strip()) for item in CodeCleaner.split_top_level_commas(m.group(2))]
            handled_exceptions:dict[str,LanFunction] = {}
            for exception_m in exceptions_blocks_ms:
                if exception_m is None: continue
                exception_name:str = exception_m.group(1); assert exception_name is not None
                if exception_name in handled_exceptions: raise LanErrors.DuplicatePropertyError("Multiple Exceptions of same Handle")
                exception_var:str|None = exception_m.group(2)
                exception_logic:str = exception_m.group(3); assert exception_logic is not None
                param_structure = {}
                if exception_var:
                    param_structure = {exception_var: LanType.string()}
                e_funct = LanFunction("Catch", LanType.nil(), param_structure, exception_logic)
                handled_exceptions[exception_name] = e_funct
            try:
                safe_block_funct = LanFunction("Try", LanType.nil(), {}, safe_block)
                safe_block_funct.execute(self, [], includeMemory=True, flags=self.InterpretFlags.TRY_CATCH)
            except LanErrors.ErrorWrapper as Error:
                e_name = type(Error.error).__name__
                if (e_name in handled_exceptions) or ("Exception" in handled_exceptions):
                    if e_name not in handled_exceptions: e_name = "Exception"
                    params = [VariableValue(LanType.string(), Error.error.message)] if len(handled_exceptions[e_name].Parameters) > 0 else []
                    handled_exceptions[e_name].execute(self, params, includeMemory=True)
                else: 
                    raise Error
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
            loop_over = self.format_parameter(m.group(2)); assert loop_over is not None
            ParamChecker.EnsureIntegrety((loop_over, LanType(LanScaffold.array)))
            loop_do_str:str = m.group(3)
            loop_var_dict:dict[str,LanType] = {}
            loop_funct = LanFunction("ForLoop", LanType.nil(), LanType.make_param_type_dict(loop_var), loop_do_str)
            if loop_over.Type != LanScaffold.array:
                raise LanErrors.WrongTypeExpectationError(f"Expected array<array>, got {loop_over.Type}")
            if unpack:
                for item in loop_over.value: 
                    ParamChecker.EnsureIntegrety((item, LanType(LanScaffold.array)))
                    if loop_over.Type != LanScaffold.array:
                        raise LanErrors.WrongTypeExpectationError(f"Expected array, got {loop_over.Type}")
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
                except LanErrors.Breaker: break
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
            raise LanErrors.Breaker()

# Main Mylange Class
class MylangeInterpreter:
    Booker:MemoryBooker
    CleanCodeCache:dict[str,str]
    LambdaCache:dict[str, tuple[str, str, str]]
    BlockTree:str
    LineNumber:int
    StartBlockCacheNumber:int
    EchosEnables:bool = False
    FilePath:str|None

    def enable_echos(self) -> None:
        self.EchosEnables = True
    
    def echo(self, *args, origin:str="MyIn", indent:int=0, anoyance:int=0) -> None:
        if not self.EchosEnables: return
        if (anoyance > 6): return
        indent += self.BlockTree.count('/')
        indentation:str = '\t'*indent
        print(f"{indentation}\033[36m[{self.LineNumber}:{origin}:{self.BlockTree}]\033[0m ", *args)

    def __init__(self, blockTree:str, startingLineNumber:int=0, startBlockCacheNumber=0, filePath:str|None=None) -> None:
        #print("\033[33m<Creating Interpreter Class>\033[0m")
        self.Booker = MemoryBooker(self)
        self.CleanCodeCache = {}
        self.BlockTree = blockTree
        self.LineNumber = startingLineNumber
        self.StartBlockCacheNumber = startBlockCacheNumber
        self.FilePath = filePath

    def make_child_block(self, parent:'MylangeInterpreter', shareMemory:bool) -> None:
        # IF these are set dirrectly, then they will allow
        # the blocks to make changes to the master's data,
        # which may not be the funcionally wanted
        # if (booker != None): self.Booker = copy.deepcopy(booker)
        if (shareMemory): self.Booker = parent.Booker
        for name, possible_import in parent.Booker._class_registry.items():
            if possible_import.Import: self.Booker.SetClass(name, possible_import)
        self.CleanCodeCache = copy.deepcopy(parent.CleanCodeCache)
        self.echo("Converting to Child Process")

    ObjectMethodMaster:LanClass|None
    
    @staticmethod
    def get_index(needle:str, haystack:str) -> list[int]:
        Return = []
        for i, line in enumerate(haystack.split("\n"), 1):
            if needle in line: Return.append(i)
        return Return
    
    class InterpretFlags(IntFlag):
        TRY_CATCH = 1 << 0

    def interpret(self, string:str, overrideClean:bool=False, objectMethodMaster:LanClass|None=None, flags:int=0) -> VariableValue|None:
        #print("INTERPRETING WITH FLAGS", flags)
        self.ObjectMethodMaster = objectMethodMaster
        try:
            return self.interpret_logic(string, overrideClean)
        except LanErrors.ErrorWrapper as errorWrap:
            raise errorWrap

    def interpret_logic(self, string:str, overrideClean:bool=False) -> VariableValue:
        lines:list[str] = self.make_chucks(string, overrideClean, self.StartBlockCacheNumber)
        Return:VariableValue = VariableValue(LanType.nil(), None); matched:bool = False
        for line_num, line in enumerate(lines):
            try:
                self.echo(line, "MyInLoop")
                # Match the type of line
                for matcher in all_matchers(LineMatcher):
                    result = matcher.match(self, line)
                    if type(result) is VariableValue:
                        matched = True
                        self.LineNumber = line_num
                        if (result.Type != LanScaffold.nil):
                            Return = result
                            break
                        elif matched:
                            break
                if not matched:
                    raise LanErrors.CannotFindQuerryError(f"Could not match self to anything: '{line}'")
            except LanErrors.MylangeError as error:
                raise LanErrors.ErrorWrapper(line, error)
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
        if self.EchosEnables:
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
    
    def format_parameter(self, part:str) -> VariableValue|None:
        part = part.strip()
        self.echo(f"Consitering: {part}", anoyance=2)
        Return:VariableValue|None = None
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
            lambda_logic = LanFunction("lambda", returnType, paramDict, blockCache)
            Return = VariableValue(LanType.callback(), lambda_logic)
        # New Object from Class #
        elif ActualRegex.NewClassObjectStatement.value.search(part):
            self.echo("Thinking of New Class Object")
            m = ActualRegex.NewClassObjectStatement.value.match(part); assert m is not None
            cls_name = m.group(1)
            cls_args = self.format_parameter_list(m.group(2))
            self.echo(f"Casted to New Class Object <{cls_name}>", anoyance=2)
            Return = self.Booker.GetClass(cls_name).create(cls_args)
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
        # Function by name and types #
        elif ActualRegex.FunctionReference.value.search(part):
            m = ActualRegex.FunctionReference.value.match(part); assert m is not None
            name = m.group(1); param_types_str = m.group(2) or m.group(3)
            if ActualRegex.CachedBlock.value.search(param_types_str): 
                param_types_str = self.CleanCodeCache[param_types_str]
            param_types = [LanType.get_type_from_typestr(item) for item in CodeCleaner.split_top_level_commas(param_types_str)]
            funct = self.Booker.GetFunction(name, param_types)
            Return = VariableValue(LanType.callback(), funct)
        # Variable by Name #
        elif ActualRegex.VariableStructure.value.search(part) and (part not in self.SpecialValueWords):
            self.echo("Somethign is here: " + part)
            if self.Booker.find(part):
                r = self.Booker.get(part)
                self.echo(f"Casted to Variable: {r}", anoyance=2)
                Return = r
            # Function #
            # TODO: This can no longer work soly off the name. It also need to 
            # work of the types of things being passed into the function.
            elif part in self.Booker.RegisteredFunctionNames:
                self.echo("Casted to Function Name")
                raise LanErrors.MylangeError("Cannot reference function by name alone. Use function call syntax.")
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
        m = re.match(r"^([\w\[\]:]+) *(?:\((.*)\))?$", string, re.UNICODE)
        if m is None: raise LanErrors.MylangeError("Something when wrong trying to parse the method")
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
        working_var:VariableValue|LanFunction|LanClass|None = None
        for i, chain_link in enumerate(method_chain):
            #print(chain_link, working_var, type(working_var))
            if chain_link[0] is None:
                working_var = self.format_parameter(chain_link[1])
            else:
                formatedParams = self.format_parameter_list(chain_link[1]) if chain_link[1] != None else []
                if type(working_var) is LanClass:
                    working_var = working_var.do_method(chain_link[0], formatedParams, self, True) #TODO AHAGAHGAHG
                elif (working_var is not None) and (type(working_var) is not VariableValue):
                    raise LanErrors.MylangeError(f"Expected Variable value, got {type(working_var)} for '{working_var}'")
                else: working_var = self.evalute_method(working_var, chain_link[0], formatedParams, i)
        assert type(working_var) is VariableValue
        return working_var
        
    def evalute_method(self, base:VariableValue|LanClass|None, methodName:str, methodParameters:list[VariableValue], chainIndex:int) -> VariableValue|LanFunction|LanClass|None:
        # Create Virtual Workspace
        Return:VariableValue|LanFunction|LanClass|None = None
        self.echo(f"Working chain -{chainIndex}-: {methodName}; {methodParameters}")
        if type(base) is LanClass:
            print("CHINA")
        elif type(base) is VariableValue and (base != None) and (base.Type == LanScaffold.casting):
            self.echo("Accessing Casting method")
            b = base.value; assert type(b) is LanClass
            Return = b.do_method(methodName, methodParameters, self) #TODO: Make sure this is right to case
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

        

        elif (methodName in self.Booker.RegisteredFunctionNames) and chainIndex == 0:
            # User-defined function
            types = [item.Type for item in methodParameters]
            funct = self.Booker.GetFunction(methodName, types)
            Return = funct.execute(self, methodParameters)
            pass
            
            
            
            
        elif (methodName in self.Booker._class_registry.keys()) and chainIndex == 0:
            #TODO: User-defined static method
            Return = self.Booker.GetClass(methodName)
        elif (self.ObjectMethodMaster and (methodName == self.ObjectMethodMaster.Name)) and chainIndex == 0:
            # Referencing a static method within the class
            Return = self.ObjectMethodMaster
        
        
        elif (self.get_cached_reference(methodName) != None) and chainIndex == 0:
            # A Random Type Instance, but cached
            Return = VariableValue(LanType.string(), self.get_cached_reference(methodName))
        elif (self.Booker.find(methodName)) and chainIndex == 0:
            # Variable, most likely as a chain base
            Return = self.Booker.get(methodName)
        else:
            # print("OMM", self.ObjectMethodMaster)
            raise LanErrors.MylangeError(f"Cannot find Function/Method/Class/Variable for method: {methodName}")
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
                        cleaned_block = re.sub(r"\n", ' ', cleaned_block, flags=re.MULTILINE)
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
    def split_top_level_commas(s, comma=',', additionalBrackets:list[tuple[str,str]]=[], stripReturns:bool=False) -> list[str]:
        result:list[str] = []
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

        if stripReturns:
            for i, res in enumerate(result): result[i] = res.strip()
        
        return result

# Custom JSON Encoder
class MylangeClassEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, VariableValue):
            return {"typeid": str(o.Type), "value": o.value}
        return json.JSONEncoder.default(self, o)