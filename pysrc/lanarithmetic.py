# IMPORTS
import re

from lanregexes import LanRe
from lantypes import RandomTypeConversions
# Handles Arithmetics of All kinds
class LanArithmetics:
    LambdaOperations = {
        "+": lambda a, b: a + b,
        "-": lambda a, b: a - b,
        "*": lambda a, b: a * b,
        "/": lambda a, b: a / b
    }
    @staticmethod
    def evalute_string(string:str) -> any:
        if re.search(LanRe.GeneralArithmetics, string):
            m = re.match(LanRe.GeneralArithmetics, string)
            left = RandomTypeConversions.convert(m.group(1))
            operation = m.group(2)
            right = RandomTypeConversions.convert(m.group(3))
            return LanArithmetics.evaluate(left, operation, right)
        else: raise Exception("Arithmetic Evaluation cannot be preformed on this string.")
    @staticmethod
    def evaluate(left:any, operation:str, right:any) -> any:
        return LanArithmetics.LambdaOperations[operation](left, right)