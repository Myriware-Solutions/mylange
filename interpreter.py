# IMPORT
import re
import json
import copy

from regexes import LanRe
from memory import MemoryBooker
from lantypes import LanTypes, VariableValue, RandomTypeConversions
from booleanlogic import LanBooleanStatementLogic
from builtinfunctions import MylangeBuiltinFunctions
# Main Mylange Class
class MylangeInterpreter:
    Booker:MemoryBooker
    CleanCodeCache:dict[str,str]
    BlockTree:str
    LineNumber:int
    def echo(this, text:str, origin:str="MyIn", indent:int=0) -> None:
        indent += this.BlockTree.count('/')
        indentation:str = '\t'*indent
        print(f"{indentation}\033[36m[{this.LineNumber}:{origin}:{this.BlockTree}]\033[0m ", text)

    def __init__(this, blockTree:str, startingLineNumber:int=0) -> None:
        print("Creating Interpreter Class")
        this.Booker = MemoryBooker()
        this.CleanCodeCache = {}
        this.BlockTree = blockTree
        this.LineNumber = startingLineNumber

    def make_child_block(this, booker:MemoryBooker, cache:dict[str,str]) -> None:
        # IF these are set dirrectly, then they will allow
        # the blocks to make changes to the master's data,
        # which may not be the funcionally wanted
        this.Booker = copy.deepcopy(booker)
        this.CleanCodeCache = copy.deepcopy(cache)
        this.echo("Converting to Child Process")

    def interpret(this, string:str, overrideClean:bool=False) -> int:
        lines:list[str] = this.make_chucks(string, overrideClean)
        for line in lines:
            this.echo(line, "MyInLoop")
            # Match the type of line
            if re.search(LanRe.VariableDecleration, line):
                m = re.match(LanRe.VariableDecleration, line)
                globally:bool = m.group(1)=="global"
                typeid:str = LanTypes.from_string(m.group(2))
                name:str = m.group(3)
                protected:bool = m.group(4).count('>') == 2
                value_str:str = m.group(5)
                value:VariableValue = VariableValue(typeid)
                value.from_string(m.group(5))
                if (value.value == None) and re.search(LanRe.FunctionOrMethodCall, value_str):
                    result:any = this.do_function_or_method(value_str)
                    value.value = result
                elif (value.value == None) and re.search(LanRe.CachedString, value_str):
                    value.value = this.CleanCodeCache[value_str][1:-1]
                #this.echo(f"This is a Variable Declaration! {globally} {protected} {typeid} {name} {value_str}", indent=1)
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
                #this.echo(f"Parts: {when_true}, {when_false}, {condition}", indent=1)
                # Evaluate the statement
                result:bool = LanBooleanStatementLogic.evaluate(condition, None)
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
            elif re.search(LanRe.FunctionOrMethodCall, line):
                this.do_function_or_method(line)
                #this.echo("This is a Function or Method Declaration!", indent=1)
                #TODO
            elif re.search(LanRe.CachedBlock, line):
                this.interpret(this.CleanCodeCache[line.strip()], True)
            this.LineNumber += 1
        #print(json.dumps(this.Booker.Registry, cls=MylangeClassEncoder))

    def make_chucks(this, string:str, overrideClean:bool=False) -> list[str]:
        clean_code, clean_code_cache = CodeCleaner.cleanup_chunk(string, overrideClean)
        this.CleanCodeCache.update(clean_code_cache)
        if this.BlockTree == "Main":
            print(f"\033[34m {clean_code} \n {json.dumps(this.CleanCodeCache)} \033[0m")
        return [item for item in clean_code.split(";") if item != '']
    
    def make_parameter_list(this, string:str) -> list:
        commas_seperated:list[str] = string.split(",")
        parts:list = []
        for part in commas_seperated:
            part = part.strip()
            tryed = RandomTypeConversions.convert(part)
            if (tryed == None) and this.Booker.find(part):
                parts.append(this.Booker.get(part).value)
            elif (tryed == None) and re.search(LanRe.FunctionOrMethodCall, part):
                parts.append(this.do_function_or_method(part))
            elif (tryed == None) and re.search(LanRe.CachedString, part):
                parts.append(this.CleanCodeCache[part][1:-1])
            else: parts.append(tryed)
        return parts
    
    def do_function_or_method(this, string:str) -> any:
        m = re.match(LanRe.FunctionOrMethodCall, string)
        function_or_method:str = m.group(1)
        parameter_blob:str = m.group(2)
        if MylangeBuiltinFunctions.is_builtin(function_or_method):
            return MylangeBuiltinFunctions.fire_builtin(this.Booker, function_or_method, this.make_parameter_list(parameter_blob))
        else: raise Exception(f"Cannot Find this Function/Method: {function_or_method}")
# Pre-processes code into interpreter-efficient executions
class CodeCleaner:
    "Converts a string of Mylange code into a execution-ready code blob."

    #(U+00A7) §

    @staticmethod
    def cleanup_chunk(string:str, preventConfine:bool=False):
        clean_code:str = CodeCleaner.remove_comments(string)
        cache:dict[str,str] = {}
        if not preventConfine:
            # first, take care of string/char values
            clean_code, qoute_cache = CodeCleaner.confine_qoutes(clean_code)
            cache.update(qoute_cache)
            # then, remove all blocks
            clean_code, block_cache = CodeCleaner.confine_brackets(clean_code)
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
    def confine_brackets(s, index_tracker=None, block_dict=None):
        if index_tracker is None:
            index_tracker = {'index': 0}
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
# Custom JSON Encoder
class MylangeClassEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, VariableValue):
            return {"typeid": obj.typeid, "value": obj.value}
        return json.JSONEncoder.default(self, obj)