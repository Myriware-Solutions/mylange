# IMPORTS
import re
from enum import StrEnum

class LanRe(StrEnum):
    # Unreconformed
    VariableDecleration = r"^(global|local)? *([a-zA-Z\[\]]+) +(\w+) *=(>+) *(.*) *"
    FunctionOrMethodCall = r"^([\w.]+) *\((.*)\)"
