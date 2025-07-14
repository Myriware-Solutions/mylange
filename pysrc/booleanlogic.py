# IMPORTS
import re

from memory import MemoryBooker
from lantypes import RandomTypeConversions
from regexes import LanRe
#from interpreter import MylangeInterpreter
# Class to Handle Boolean Logic Statements
class LanBooleanStatementLogic:
    LambdaOperations = {
        "==": lambda l, r: l == r,
        "!=": lambda l, r: l != r,
        "<" : lambda l, r: l < r,
        "<=": lambda l, r: l <= r,
        ">" : lambda l, r: l > r,
        ">=": lambda l, r: l >= r
    }
    @staticmethod
    def evalute_string(string:str) -> any:
        # Check against Equality (==, <, <=, >, >=, !=)
        if re.search(LanRe.GeneralEqualityStatement, string):
            m = re.match(LanRe.GeneralEqualityStatement, string)
            #TODO: Convert these into Antomonus Casted values
            left = RandomTypeConversions.convert(m.group(1))
            operation = m.group(2)
            right = RandomTypeConversions.convert(m.group(3))
            return LanBooleanStatementLogic.evaluate(left, operation, right)
        else: raise Exception("Boolean Evaluation cannot be preformed on this string.")
    @staticmethod
    def evaluate(left:any, operation:str, right:any) -> bool:
        return LanBooleanStatementLogic.LambdaOperations[operation](left, right)