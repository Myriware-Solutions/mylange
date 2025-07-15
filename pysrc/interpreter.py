# IMPORT
import re
import json
import copy
import sys

from lanregexes import LanRe
from memory import MemoryBooker
from lantypes import LanTypes, VariableValue, RandomTypeConversions
from booleanlogic import LanBooleanStatementLogic
from lanarithmetic import LanArithmetics
from builtinfunctions import MylangeBuiltinFunctions, VariableTypeMethods
from lanerrors import LanErrors
from interface import AnsiColor
# GLOBALS
FILE_EXT:str = ".my"
# Main Mylange Class
class MylangeInterpreter:
    Booker:MemoryBooker
    CleanCodeCache:dict[str,str]
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
        this.Fuctions:dict[str,FunctionStatement] = {}

    def make_child_block(this, booker:MemoryBooker, cache:dict[str,str]) -> None:
        # IF these are set dirrectly, then they will allow
        # the blocks to make changes to the master's data,
        # which may not be the funcionally wanted
        # if (booker != None): this.Booker = copy.deepcopy(booker)
        if (booker != None): this.Booker = booker
        this.CleanCodeCache = copy.deepcopy(cache)
        this.echo("Converting to Child Process")

    def interpret(this, string:str, overrideClean:bool=False) -> any:
        try:
            return this.interpret_logic(string, overrideClean)
        except LanErrors.Break: raise LanErrors.Break()
        except LanErrors.MylangeError as exception:
            AnsiColor.println(f"Fatal Error: {exception.message}", AnsiColor.BRIGHT_RED)
            return None

    def interpret_logic(this, string:str, overrideClean:bool=False) -> any:
        lines:list[str] = this.make_chucks(string, overrideClean, this.StartBlockCacheNumber)
        Return:any = None
        for line in lines:
            this.echo(line, "MyInLoop")
            # Match the type of line
            if re.search(LanRe.ImportStatement, line):
                m = re.match(LanRe.ImportStatement, line)
                file_name:str = m.group(1) + FILE_EXT
                this.echo(f"Importing from {file_name}", "Importer")
                function_bloc:str = m.group(2)
                functions = [funct.strip() for funct in function_bloc.split(",")]
                # Setup Vitual envirement
                mi = MylangeInterpreter(f"Imports\\{m.group(1)}", startBlockCacheNumber=len([item for item in this.CleanCodeCache.keys() if item.startswith("0x")]))
                mi.make_child_block(None, this.CleanCodeCache)
                with open(file_name, 'r') as imports_file:
                    mi.interpret(imports_file.read())
                    for funct_name in functions:
                        this.Fuctions[funct_name] = mi.Fuctions[funct_name]
                    this.CleanCodeCache.update(mi.CleanCodeCache)
            elif re.search(LanRe.VariableDecleration, line):
                m = re.match(LanRe.VariableDecleration, line)
                #globally:bool = m.group(1)=="global"
                typeid:int = LanTypes.from_string(m.group(2))
                name:str = m.group(3)
                #protected:bool = m.group(4).count('>') == 2
                value_str:str = m.group(5)
                value:VariableValue = VariableValue(typeid)
                value.value = this.format_parameter(value_str)
                this.echo(f"This is a Variable Declaration! {name}@{typeid}({m.group(2)}) {value.value}", indent=1)
                this.Booker.set(name, value)
            elif re.search(LanRe.IfStatementGeneral, line):
                # Match to correct if/else block
                condition = None
                when_true = None 
                when_false = None
                if re.search(LanRe.IfElseStatement, line):
                    m = re.match(LanRe.IfElseStatement, line)
                    condition = m.group(1)
                    when_true = m.group(2)
                    when_false = m.group(3)
                elif re.search(LanRe.IfStatement, line):
                    m = re.match(LanRe.IfStatement, line)
                    condition = m.group(1)
                    when_true = m.group(2)
                else:
                    raise Exception("IF/Else statement not configured right!")
                this.echo(f"Parts: {when_true}, {when_false}, {condition}", indent=1)
                # Evaluate the statement
                result = this.format_parameter(condition)
                if type(result) != bool:
                    raise LanErrors.ConditionalNotBoolError(f"Cannot use this for boolean logic ({type(result)} {result}): {condition}")
                # Do functions
                if (result):
                    block = MylangeInterpreter(f"{this.BlockTree}/IfTrue", this.LineNumber)
                    block.make_child_block(this.Booker, this.CleanCodeCache)
                    block.interpret(when_true, True)
                elif (not result) and (when_false!=None):
                    block = MylangeInterpreter(f"{this.BlockTree}/IfFalse", this.LineNumber)
                    block.make_child_block(this.Booker, this.CleanCodeCache)
                    block.interpret(when_false, True)
            elif re.search(LanRe.FunctionStatement, line):
                m = re.match(LanRe.FunctionStatement, line)
                return_type:str = m.group(1)
                function_name:str = m.group(2)
                function_parameters_string = m.group(3)
                function_code_string = m.group(4)
                funct = FunctionStatement(function_name, return_type, function_parameters_string, function_code_string)
                this.Fuctions[function_name] = funct
            elif re.search(LanRe.ForStatement, line):
                m = re.match(LanRe.ForStatement, line)
                loop_var = f"{m.group(1).strip()} {m.group(2).strip()}"
                loop_over:list = this.format_parameter(m.group(3))
                loop_do_str:str = m.group(4)
                loop_funct = FunctionStatement("ForLoop", "nil", loop_var, loop_do_str)
                try:
                    for item in loop_over: loop_funct.execute(this, [item], True)
                except LanErrors.Break: pass

            elif re.search(LanRe.WhileStatement, line):
                while_m = re.match(LanRe.WhileStatement, line)
                while_condition = while_m.group(1).strip()
                while_do_str = while_m.group(2).strip()
                while_loop_funct = FunctionStatement("WhileLoop", "nil", "", while_do_str)
                try:
                    while this.format_parameter(while_condition):
                        while_loop_funct.execute(this, [], True)
                except LanErrors.Break: pass

            elif re.search(LanRe.FunctionOrMethodCall, line):
                this.do_function_or_method(line)
            elif re.search(LanRe.CachedBlock, line):
                r = this.interpret(this.CleanCodeCache[line.strip()], True)
                if (r != None): Return = r
            elif re.search(LanRe.BreakStatement, line):
                this.echo("Break Called")
                raise LanErrors.Break()
            elif re.search(LanRe.ReturnStatement, line):
                # Last thing, return forced
                m = re.match(LanRe.ReturnStatement, line)
                Return = this.format_parameter(m.group(1))
                return Return
            this.LineNumber += 1
        return Return

    def make_chucks(this, string:str, overrideClean:bool=False, starBlockCacheNumber=0) -> list[str]:
        clean_code, clean_code_cache = CodeCleaner.cleanup_chunk(string, overrideClean, starBlockCacheNumber)
        this.CleanCodeCache.update(clean_code_cache)
        if (this.BlockTree == "Main") and this.EchosEnables:
            mem_blocks:list[str] = [f"{k} -> {v}" for k, v in this.CleanCodeCache.items()]
            AnsiColor.println(f"[Code Lines]\n{clean_code}\n[Memory Units]\n{'\n'.join(mem_blocks)}", AnsiColor.BLUE)
        return [item for item in clean_code.split(";") if item != '']
    
    def make_parameter_list(this, string:str) -> list:
        commas_seperated:list[str] = CodeCleaner.split_top_level_commas(string)
        parts:list = []
        for part in commas_seperated:
            parts.append(this.format_parameter(part))
        return parts
    
    def format_parameter(this, part:str) -> any:
        part = part.strip()
        this.echo(f"Consitering: {part}", anoyance=2)
        if RandomTypeConversions.get_type(part)[0] != 0:
            this.echo("Casted to RandomType", anoyance=2)
            return RandomTypeConversions.convert(part, this)
        
        elif re.search(LanRe.GeneralEqualityStatement, part):
            m = re.match(LanRe.GeneralEqualityStatement, part)
            r = LanBooleanStatementLogic.evaluate(
                this.format_parameter(m.group(1)),
                m.group(2),
                this.format_parameter(m.group(3))
            )
            this.echo(f"Casted to Boolean Expression: {r}", anoyance=2)
            return r
        elif re.search(LanRe.GeneralArithmetics, part):
            m = re.match(LanRe.GeneralArithmetics, part)
            this.echo("Casted to Arithmetic Expression", anoyance=2)
            return LanArithmetics.evaluate(
                this.format_parameter(m.group(1)),
                m.group(2),
                this.format_parameter(m.group(3))
            )
        
        elif re.search(LanRe.FunctionOrMethodCall, part):
            this.echo("Casted to Function/Method", anoyance=2)
            return this.do_function_or_method(part)

        elif re.search(LanRe.CachedString, part):
            this.echo("Casted to Cached String", anoyance=2)
            return this.CleanCodeCache[part][1:-1]
        elif re.search(LanRe.IndexedVariableName, part):
            this.echo("Casted to Indexed Variable", anoyance=2)
            indexed_m = re.match(LanRe.IndexedVariableName, part)
            if this.Booker.find(indexed_m.group(1)):
                var:VariableValue = this.Booker.get(indexed_m.group(1))
                if (LanTypes.is_indexable(var.typeid)):
                    return var.value[int(indexed_m.group(2))]
                else: raise LanErrors.NotIndexableError(f"Cannot Index non-indexable variable: {part}")
            else: raise LanErrors.MemoryMissingError(f"Cannot find indexed variable by name: {part}")

        elif re.search(LanRe.SetIndexedVariableName, part):
            set_indexed_m = re.match(LanRe.SetIndexedVariableName, part)
            if this.Booker.find(set_indexed_m.group(1)):
                var:VariableValue = this.Booker.get(set_indexed_m.group(1))
                if (var.typeid == LanTypes.set):
                    return var.value[set_indexed_m.group(2)]
                else: raise LanErrors.NotIndexableError(f"Cannot Set Index non-indexable variable: {part}")
            else: raise LanErrors.MemoryMissingError(f"Cannot find indexed variable by name: {part}")

        elif re.search(LanRe.VariableName, part) and (part not in this.SpecialValueWords):
            if this.Booker.find(part):
                r = this.Booker.get(part).value
                this.echo(f"Casted to Variable: {r}", anoyance=2)
                return r
            else: raise LanErrors.MemoryMissingError(f"Cannot find variable by name: {part}")
        else:
            this.echo("Casted to Failsafe RandomType Conversion", anoyance=2)
            return RandomTypeConversions.convert(part, this)
        
    def evaluate_boolean(this, condition:str) -> bool:
        if re.search(LanRe.GeneralEqualityStatement, condition):
            bool_m = re.match(LanRe.GeneralEqualityStatement, condition)
            left:any = this.format_parameter(bool_m.group(1))
            operation:str = bool_m.group(2)
            right:any = this.format_parameter(bool_m.group(3))
            return LanBooleanStatementLogic.evaluate(left, operation, right)
        

    # Certain variable-name capatible words that should not
    # be ever treated like a variable.
    SpecialValueWords:list[str] = ["nil", "true", "false"]
    
    def do_function_or_method(this, string:str) -> any:
        m = re.match(LanRe.FunctionOrMethodCall, string)
        function_or_method:str = m.group(1)
        parameter_blob:str = m.group(2)
        parameters_formated = this.make_parameter_list(parameter_blob)
        if MylangeBuiltinFunctions.is_builtin(function_or_method):
            return MylangeBuiltinFunctions.fire_builtin(this.Booker, function_or_method, parameters_formated)
        elif function_or_method in this.Fuctions.keys():
            parameters = this.make_parameter_list(parameter_blob)
            r = this.Fuctions[function_or_method].execute(this, parameters)
            return r
        elif '.' in function_or_method:
            # Indicates Method call
            nodes:list[str] = function_or_method.split('.')
            # Decide whether the first node is a variable, or class
            if this.Booker.find(nodes[0]):
                # Call a type method on the variable
                var = this.Booker.get(nodes[0])
                this.echo(f"Node here {var}")
                r = VariableTypeMethods.fire_variable_method(nodes[1], var, parameters_formated)
                this.echo(f"Altr here {var}")
                return r
            else:
                #TODO: Find the class, then do the method
                pass
        else: raise Exception(f"Cannot Find this Function/Method: {function_or_method}")

class FunctionStatement:
    Name:str
    ReturnType:int
    Parameters:dict[str,int]
    Code:str
    def __init__(this, fName:str, fReturnType:str, fParamString:str, fCode:str):
        this.Parameters = {}
        this.Name = fName
        this.ReturnType = LanTypes.from_string(fReturnType)
        for set in fParamString.split(","):
            if set == "": continue
            set_parts = set.strip().split(" ")
            this.Parameters[set_parts[1]] = LanTypes.from_string(set_parts[0])
        this.Code = fCode
    
    def execute(this, parent:MylangeInterpreter, params:list, includeMemory:bool=False) -> any:
        container = MylangeInterpreter(f"Funct\\{this.Name}")
        if parent.EchosEnables: container.enable_echos()
        old_mem_keys:list[str] = []
        mem = None
        if includeMemory:
            mem = parent.Booker
            old_mem_keys = list(parent.Booker.Registry.keys())
        container.make_child_block(mem, parent.CleanCodeCache)
        # Add parameters
        for i, param in enumerate(this.Parameters.items()):
            varval = VariableValue(param[1])
            varval.value = params[i] #TODO: Ensure values match
            container.Booker.set(param[0], varval)
        r:any = None
        thorw_break = False
        try: 
            r = container.interpret(this.Code, True)
        except LanErrors.Break: thorw_break = True
        # Clear New Memory values, keeping old or altered ones
        if includeMemory: 
            for key in list(parent.Booker.Registry.keys()):
                if key not in old_mem_keys: del parent.Booker.Registry[key]
        if thorw_break: raise LanErrors.Break()
        return r


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
    
    @staticmethod
    def split_top_level_commas(s) -> list[str]:
        result = []
        depth = 0
        current = []

        for char in s:
            if char == ',' and depth == 0:
                result.append(''.join(current))
                current = []
            else:
                if char == '(':
                    depth += 1
                elif char == ')':
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