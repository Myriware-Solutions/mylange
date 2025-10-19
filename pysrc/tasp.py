### IMPORTS ###
# Python #
import sys, json, re
# Libraries #
# Local #
from lantypes import VariableValue, RandomTypeConversions, LanTypes
from interpreter import CodeCleaner
### CODE ###

class TableSpeak:
    
    BodyRegex = re.compile(r"(?:<([\w\W]+)>)?\s*([\w\W]+)")
    
    @classmethod
    def GetHeadersAndBody(cls, string:str) -> tuple[str|None,str]:
        m = cls.BodyRegex.match(string)
        if not m: raise Exception("Cannot find head/body match!")
        return m.group(1), m.group(2)
    
    @staticmethod
    def MakeColonPairs(string:str) -> list[tuple[str,str|None]]:
        pairs = CodeCleaner.split_top_level_commas(string, ";")
        def splits(s:str):
            ss= s.split(":")
            return (ss[0], ss[1] if len(ss) == 2 else None)
        r = [splits(pair) for pair in pairs]
        return r
    
    @classmethod
    def InterpretFile(cls, path:str) -> None:
        with open(path, 'r') as f:
            return cls.Interpret(f.read())
    
    @classmethod
    def Interpret(cls, taspString:str) -> None:
        cleaned, cache = CodeCleaner.cleanup_chunk(taspString)
        print(cleaned, "\n\n", json.dumps(cache, indent=2))
        if "0x0" not in cache: raise Exception("Cannot find enclosing brackets.")
        header, body = cls.GetHeadersAndBody(re.sub(r"\s", "", cache["0x0"]))
        if header is not None:
            # process the headers
            h_list = cls.MakeColonPairs(header)
            pass
        
        # process the body
        
        
        
        
class TaspHeaderOptions:
    Mode:int
    Cols:list[str]|None
    def __init__(self):
        self.Mode = 0
        self.Cols = None
        pass
    
    def Init(opts:list[str,str|None]) -> None:
        
        for opt in opts:
            match opt:
                case 'row-col':pass
        

# Notes
# TASP, or tablespeak, is a simple or complex object definition language.
# It takes both elements from CSV and JSON, and can be used, and should be,
# in Myriware Mylange.

### DEBUG ###

if __name__ == "__main__":
    TableSpeak.InterpretFile(sys.argv[1])