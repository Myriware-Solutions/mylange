### IMPORTS ###
# Python #
from enum import Enum
### CODE ###
class EffectString:
    String:str
    Color:'AnsiColor'
    def __init__(self, color:'AnsiColor', string:str) -> None:
        self.String = string
        self.Color = color
    def __repr__(self) -> str:
        return f"{self.Color.value}{self.String}{AnsiColor.RESET.value}"
    def __add__(self, other:'EffectString|str') -> str:
        return self.__repr__() + str(other)
    def __radd__(self, other:str) -> str:
        return other + self.__repr__()

class AnsiColor(Enum):
    """Allows easy manipulation of strings for colorful terminal output. Simply multiply (*) a string
    by one of the enums, and print it!"""
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    def __rmul__(self, other:str) -> EffectString:
        """Returns a ColorString Object containing
        the string and color information.

        Args:
            other (str): String to print.

        Returns:
            ColorString: ColorString object containing string and color info.
        """
        if isinstance(other, str): return EffectString(self, other)
        return NotImplemented