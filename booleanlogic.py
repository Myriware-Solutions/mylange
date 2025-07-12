# IMPORTS
import re
from enum import StrEnum
from memory import MemoryBooker
from lantypes import RandomTypeConversions
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
    def evaluate(string:str, masterBooker:MemoryBooker) -> bool:
        # Check against Equality (==, <, <=, >, >=, !=)
        if re.search(BooleanStatements.GeneralEqualityStatement, string):
            m = re.match(BooleanStatements.GeneralEqualityStatement, string)
            #TODO: Convert these into Antomonus Casted values
            left = RandomTypeConversions.convert(m.group(1))
            operation = m.group(2)
            right = RandomTypeConversions.convert(m.group(3))
            return LanBooleanStatementLogic.LambdaOperations[operation](left, right)
        # Check against singles
        pass



class BooleanStatements(StrEnum):
    GeneralEqualityStatement = r"(.*?) *([=<>!]+) *(.*)"