# IMPORT
import re
import json
import copy

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
    
    def echo(this, text:str, origin:str="MyIn", indent:int=0) -> None:
        if not this.EchosEnables: return
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
        if (booker != None): this.Booker = copy.deepcopy(booker)
        this.CleanCodeCache = copy.deepcopy(cache)
        this.echo("Converting to Child Process")

    def interpret(this, string:str, overrideClean:bool=False) -> any:
        try:
            return this.interpret_logic(string, overrideClean)
        except LanErrors.MemoryMissingError as exception:
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
                typeid:str = LanTypes.from_string(m.group(2))
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
                bool_m = re.match(LanRe.GeneralEqualityStatement, condition)
                left:any = this.format_parameter(bool_m.group(1))
                operation:str = bool_m.group(2)
                right:any = this.format_parameter(bool_m.group(3))
                result:bool = LanBooleanStatementLogic.evaluate(left, operation, right)
                #this.echo(f"Evaluation: {result}", indent=1)
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
            elif re.search(LanRe.FunctionOrMethodCall, line):
                this.do_function_or_method(line)
            elif re.search(LanRe.CachedBlock, line):
                r = this.interpret(this.CleanCodeCache[line.strip()], True)
                if (r != None): Return = r
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
        if RandomTypeConversions.get_type(part)[0] != 0:
            return RandomTypeConversions.convert(part, this)
        elif re.search(LanRe.FunctionOrMethodCall, part):
            return this.do_function_or_method(part)
        elif re.search(LanRe.GeneralEqualityStatement, part):
            m = re.match(LanRe.GeneralEqualityStatement, part)
            return LanBooleanStatementLogic.evaluate(
                this.format_parameter(m.group(1)),
                m.group(2),
                this.format_parameter(m.group(3))
            )
        elif re.search(LanRe.GeneralArithmetics, part):
            m = re.match(LanRe.GeneralArithmetics, part)
            return LanArithmetics.evaluate(
                this.format_parameter(m.group(1)),
                m.group(2),
                this.format_parameter(m.group(3))
            )
        elif re.search(LanRe.CachedString, part):
            return this.CleanCodeCache[part][1:-1]
        elif re.search(LanRe.VariableName, part) and (part not in this.SpecialValueWords):
            if this.Booker.find(part):
                return this.Booker.get(part).value
            else: raise LanErrors.MemoryMissingError(f"Cannot find variable by name: {part}")
        else:
            return RandomTypeConversions.convert(part, this)

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
                print("Node here", var)
                r = VariableTypeMethods.fire_variable_method(nodes[1], var, parameters_formated)
                return r
            else:
                #TODO: Find the class, then do the method
                pass
        else: raise Exception(f"Cannot Find this Function/Method: {function_or_method}")

class FunctionStatement:
    Name:str
    ReturnType:int
    Parameters:dict[str,int] = {}
    Code:str
    def __init__(this, fName:str, fReturnType:str, fParamString:str, fCode:str):
        this.Name = fName
        this.ReturnType = LanTypes.from_string(fReturnType)
        for set in fParamString.split(","):
            set_parts = set.strip().split(" ")
            this.Parameters[set_parts[1]] = LanTypes.from_string(set_parts[0])
        this.Code = fCode
    
    def execute(this, parent:MylangeInterpreter, params) -> any:
        container = MylangeInterpreter(f"Funct\\{this.Name}")
        container.make_child_block(None, parent.CleanCodeCache)
        for i, param in enumerate(this.Parameters.items()):
            varval = VariableValue(param[1])
            varval.value = params[i] #TODO: Ensure values match
            container.Booker.set(param[0], varval)
        r = container.interpret(this.Code, True)
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