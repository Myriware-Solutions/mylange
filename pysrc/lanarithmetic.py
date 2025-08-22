from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from interpreter import MylangeInterpreter
# IMPORTS
from lanregexes import ActualRegex
from lantypes import LanTypes, RandomTypeConversions
from lantypes import VariableValue
from builtinfunctions import EnsureIntegrety, GetTypesOfParameters

NIL_RETURN:VariableValue = VariableValue(LanTypes.nil, None)
# Handles Arithmetics of All kinds
class LanArithmetics:
    @staticmethod
    def withInts(a:VariableValue, b:VariableValue, callback) -> VariableValue:
        EnsureIntegrety((a, LanTypes.integer), (b, LanTypes.integer))
        return VariableValue(LanTypes.integer, callback(a.value, b.value))
    
    @staticmethod
    def concentrateStrings(a:VariableValue, b:VariableValue) -> VariableValue:
        types = GetTypesOfParameters(a, b)
        match types:
            case [LanTypes.string, LanTypes.string]:
                return a.value + b.value
            case [LanTypes.string, LanTypes.integer]:
                return a.value * b.value
            case _:
                raise Exception("Cannot perform operations on these!")
            
    @staticmethod
    def booleanStatement(a:VariableValue, b:VariableValue, callback) -> VariableValue:
        return VariableValue(LanTypes.boolean, callback(a.value, b.value))

    LambdaOperations = {
        "+":  lambda a, b: LanArithmetics.withInts(a, b, (lambda a, b: a + b)),
        "-":  lambda a, b: LanArithmetics.withInts(a, b, (lambda a, b: a - b)),
        "*":  lambda a, b: LanArithmetics.withInts(a, b, (lambda a, b: a * b)),
        "/":  lambda a, b: LanArithmetics.withInts(a, b, (lambda a, b: a / b)),
        "..": lambda a, b: LanArithmetics.concentrateStrings(a, b),
        "==": lambda l, r: LanArithmetics.booleanStatement(l, r, (lambda l, r: l == r)),
        "!=": lambda l, r: LanArithmetics.booleanStatement(l, r, (lambda l, r: l != r)),
        "<" : lambda l, r: LanArithmetics.booleanStatement(l, r, (lambda l, r: l < r)),
        "<=": lambda l, r: LanArithmetics.booleanStatement(l, r, (lambda l, r: l <= r)),
        ">" : lambda l, r: LanArithmetics.booleanStatement(l, r, (lambda l, r: l > r)),
        ">=": lambda l, r: LanArithmetics.booleanStatement(l, r, (lambda l, r: l >= r))
    }

    @staticmethod
    def evalute_string(parent:'MylangeInterpreter', string:str) -> VariableValue:
        evaluation_chain = LanArithmetics.parse_expression(string)
        if (evaluation_chain == None): raise Exception("Could not parse the arithmetic expression")
        working_link:VariableValue = None
        for i, link in enumerate(evaluation_chain):
            if i == 0:
                working_link = parent.format_parameter(link[1])
            else:
                next_link = parent.format_parameter(link[1])
                working_link = LanArithmetics.evaluate(working_link, link[0].strip(), next_link, i)
        return working_link
    
    @staticmethod
    def evaluate(left:VariableValue, operation:str, right:VariableValue, chainIndex:int) -> VariableValue:
        try: return LanArithmetics.LambdaOperations[operation](left, right)
        except: raise Exception(f"Problem with arithmetic operation on chain link {chainIndex}")

    @staticmethod
    def is_arithmetic(expr:str, operators=None) -> bool:
        if LanArithmetics.parse_expression(expr, operators) == None: return False
        return True

    @staticmethod
    def parse_expression(expr:str, operators=None, begin_symbols=None):
        if operators is None:
            operators = list(LanArithmetics.LambdaOperations.keys())
        if begin_symbols is None:
            begin_symbols = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'"}

        expr = expr.strip()
        if not expr:
            return None

        # --- Balance check (parentheses/quotes) ---
        stack = []
        quotes = {'"': '"', "'": "'"}
        pairs = {'(': ')', '[': ']', '{': '}'}

        for ch in expr:
            if ch in quotes:
                if stack and stack[-1] == quotes[ch]:
                    stack.pop()
                else:
                    stack.append(quotes[ch])
            elif stack and stack[-1] in quotes.values():
                continue
            elif ch in pairs:
                stack.append(pairs[ch])
            elif stack and ch == stack[-1]:
                stack.pop()

        if stack:  # unbalanced
            return None

        # --- Split logic ---
        result = []
        current = []
        last_delim = None
        stack = []

        i = 0
        found_operator = False
        while i < len(expr):
            ch = expr[i]

            if ch in begin_symbols:
                stack.append(begin_symbols[ch])
                current.append(ch)
            elif stack and ch == stack[-1]:
                stack.pop()
                current.append(ch)
            elif stack and stack[-1] in begin_symbols.values():
                current.append(ch)
            else:
                matched_op = None
                for op in operators:
                    if expr.startswith(op, i) and not stack:
                        matched_op = op
                        break
                if matched_op:
                    found_operator = True
                    segment = "".join(current).strip()
                    if segment or last_delim is not None:
                        result.append((last_delim, segment))
                    current = []
                    last_delim = matched_op
                    i += len(matched_op)
                    continue
                else:
                    current.append(ch)
            i += 1

        # final flush
        segment = "".join(current).strip()
        if segment or last_delim is not None:
            result.append((last_delim, segment))

        # Must have at least 2 operands and one operator
        if not found_operator or len([r for _, r in result if r]) < 2:
            return None

        return result

