# IMPORT
import re
import json
from regexes import LanRe
from memory import MemoryBooker
from lantypes import LanTypes, VariableValue
# Main Mylange Class

class MylangeInterpreter:
    Booker:MemoryBooker
    CleanCodeCache:dict[str,str]
    def echo(this, text:str, origin:str="MyIn", indent:int=0) -> None:
        indentation:str = '\t'*indent
        print(f"{indentation}[{origin}] ", text)

    def __init__(this) -> None:
        this.echo("Creating Interpreter Class")
        this.Booker = MemoryBooker()

    def interpret(this, string:str) -> int:
        lines:list[str] = this.make_chucks(string)
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

                this.echo(f"This is a Variable Declaration! {globally} {protected} {typeid} {name} {value_str}", indent=1)
                this.Booker.set(name, value)
            # If/else statements here
            elif re.search(LanRe.FunctionOrMethodCall, line):
                this.echo("This is a Function or Method Declaration!", indent=1)
        print(json.dumps(this.Booker.Registry, cls=MylangeClassEncoder))

    def make_chucks(this, string:str) -> list[str]:
        clean_code, this.CleanCodeCache = CodeCleaner.cleanup_chunk(string)
        return clean_code.split(";")

class CodeCleaner:
    "Converts a string of Mylange code into a execution-ready code blob."

    #(U+00A7) §

    @staticmethod
    def cleanup_chunk(string:str):
        clean_code:str = ""
        cache:dict[str,str] = {}
        # first, take care of string/char values
        clean_code, qoute_cache = CodeCleaner.confine_qoutes(string)
        cache.update(qoute_cache)
        # then, remove all blocks
        clean_code, block_cache = CodeCleaner.confine_brackets(string)
        cache.update(block_cache)
        # remove all return lines
        clean_code = clean_code.replace('\n', '')
        return clean_code, cache

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
                        cleaned_block = '{' + replaced_inner + '}'
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


    
class MylangeClassEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, VariableValue):
            return {"typeid": obj.typeid, "value": obj.value}
        return json.JSONEncoder.default(self, obj)