### IMPORTS ###
# Python #
import sys, json, re
# Libraries #
# Local #
from lantypes import VariableValue, RandomTypeConversions, LanType, LanScaffold
from interpreter import CodeCleaner, MylangeClassEncoder, MylangeInterpreter
from interface import AnsiColor
### CODE ###

class TableSpeak:
    
    BodyRegex = re.compile(r"(?:<([\w\W<>]+)>)?\s*([\w\W]+)")
    KeysRowItemRegex = re.compile(r"\((\w+)\)")
    
    class TaspArray(list[VariableValue|str]): pass
    class TaspDoubleArray(list[TaspArray]): pass
    class TaspListObject(dict[str,TaspArray]): pass
    class TaspObjectList(list[dict[str,VariableValue]]): pass
    class ComplexTaspObject(dict[str,dict[str,VariableValue|str]]): pass
    
    type TaspLike = TaspArray|TaspDoubleArray|TaspListObject|TaspObjectList|ComplexTaspObject|None
    
    Data:TaspLike
    Header:'TaspHeaderOptions'
    Indent:str
    
    def __init__(self, indent="  ") -> None:
        self.Indent = indent
        self.Data=None
    
    @classmethod
    def _get_headers_and_body(cls, string:str) -> tuple[str|None,str]:
        m = cls.BodyRegex.match(string)
        if not m: raise Exception("Cannot find head/body match!")
        return m.group(1), m.group(2)
    
    @staticmethod
    def _make_colon_pairs(string:str) -> list[tuple[str,str|None]]:
        pairs = CodeCleaner.split_top_level_commas(string, ";")
        def splits(s:str):
            ss= s.split(":")
            return (ss[0], ss[1] if len(ss) == 2 else None)
        r = [splits(pair) for pair in pairs]
        return r
    
    @classmethod
    def _get_columns(cls, obj:TaspDoubleArray) -> TaspDoubleArray:
        ret = cls.TaspDoubleArray()
        # settup the object
        for col in obj[0]: ret.append(cls.TaspArray())
        for row in obj:
            for j, col in enumerate(row):
                ret[j].append(col)
                pass
        return ret
    
    def InterpretFile(self, path:str) -> None:
        with open(path, 'r') as f:
            return self.Interpret(f.read())
    
    def Interpret(self, taspString:str) -> None:
        _, cache = CodeCleaner.cleanup_chunk(taspString)
        mi = MylangeInterpreter("TASP Sub-Process")
        mi.CleanCodeCache=cache
        if "0x0" not in cache: raise Exception("Cannot find enclosing brackets.")
        header, body = self._get_headers_and_body(re.sub(r"\s", "", cache["0x0"]))
        if header is None: raise Exception("There needs to be a header for the tasp object")
        # process the headers
        self.Header = TaspHeaderOptions(self._make_colon_pairs(header))
        # process the body
        # Make the main matrix first
        matrix:TableSpeak.TaspDoubleArray = self.TaspDoubleArray()
        for i, row_str in enumerate(CodeCleaner.split_top_level_commas(body, ";")):
            row = self.TaspArray() # Make the row a new list, or just just the matrix if mode is linear.
            for j, col_str in enumerate(CodeCleaner.split_top_level_commas(row_str)):
                #TODO: intercept the string and make it the value it should be
                if (self.Header.Schema is None):
                    if self.Header.KeysRow is not None:
                        row.append(col_str)
                    else:
                        var = mi.format_parameter(col_str); assert type(var) is VariableValue
                        row.append(var)
                elif ((type(self.Header.Schema[j]) is not LanType) and (self.Header.Schema[j] == -1)) or (i == self.Header.KeysRow): row.append(col_str)
                else:
                    var=mi.format_parameter(col_str)
                    assert type(var) == VariableValue
                    assert var.Type == self.Header.Schema[j] # Make sure the value makes sense with the schema.
                    row.append(var)
            matrix.append(row)
        # Then, the specific cases can be processed.
        Return:TableSpeak.TaspLike = None
        match self.Header.Mode:
            case 0:
                Return = self.TaspArray()
                for row in matrix: Return += row # type: ignore # type : ignore
            case 1:
                Return = self.TaspDoubleArray()
                for row in matrix: Return.append(row) # type: ignore # type : ignore
            case 2:
                assert self.Header.KeysRow is not None
                Return = self.TaspListObject()
                column_matrix = self._get_columns(matrix)
                for column in column_matrix:
                    c_name = column[self.Header.KeysRow]; assert type(c_name) is str
                    m = self.KeysRowItemRegex.match(c_name); assert m is not None
                    del column[self.Header.KeysRow]
                    Return[m.group(1)] = column
            case 3:
                assert self.Header.KeysRow is not None
                Return = self.TaspObjectList()
                row_keys = []
                for row_key in matrix[self.Header.KeysRow]: 
                    assert type(row_key) is str; 
                    m=self.KeysRowItemRegex.match(row_key); assert m is not None
                    row_keys.append(m.group(1))
                del matrix[self.Header.KeysRow] # Remove keys row
                for row_list in matrix:
                    d_row:dict[str,VariableValue] = {}
                    for i, col in enumerate(row_list): assert type(col) is VariableValue; d_row[row_keys[i]] = col
                    Return.append(d_row)
            case 4:
                assert self.Header.KeysRow is not None; assert self.Header.RowKey is not None
                Return = self.ComplexTaspObject()
                row_keys:list[str] = []
                for k, item in enumerate(matrix[self.Header.KeysRow]):
                    if k == self.Header.RowKey: continue # skip the place where the key of the row would be
                    assert type(item) is str
                    m = self.KeysRowItemRegex.match(item); assert m is not None
                    row_keys.append(m.group(1))
                for i, row_list in enumerate(matrix):
                    if i == self.Header.KeysRow: continue
                    # Get the name of the row
                    r_name = row_list[self.Header.RowKey]; assert type(r_name) is str
                    del row_list[self.Header.RowKey] # remove the row name for values to loop through
                    rrow:dict[str,VariableValue|str] = {}
                    for j, col in enumerate(row_list):
                        assert type(col) is VariableValue
                        # First, get the value of the key for the col
                        rrow[row_keys[j]] = col
                        pass
                    Return[r_name] = rrow
        assert Return is not None
        self.Data = Return
    
    def __str__(self) -> str:
        Return:list[str] = []
        Return.append("[Tasp Object]")
        Return.append(str(self.Header))
        match self.Data:
            case TableSpeak.TaspArray():
                Return.append(", ".join([str(item) for item in self.Data]))
            case TableSpeak.TaspDoubleArray():
                for i,row in enumerate(self.Data):
                    Return.append(f"[{i}] " + ", ".join([str(item) for item in row]))
            case TableSpeak.TaspListObject():
                for key, column in self.Data.items():
                    Return.append(f"[{key}] "+", ".join([str(item) for item in column]))
            case TableSpeak.TaspObjectList():
                for i, row in enumerate(self.Data):
                    Return.append(f"[{i}]")
                    for key, col in row.items():
                        Return.append(f"{key}=>col")
            case TableSpeak.ComplexTaspObject():
                for row_name, row in self.Data.items():
                    Return.append(f"{row_name}")
                    for col_name, col in row.items():
                        Return.append(f"{self.Indent}{col_name} => {col}")
            case _: raise Exception("I needed a TaspLike object, got: ", type(self.Data))
        Return.append("[-----------]")
        return "\n".join(Return)
    
    def __repr__(self) -> str:
        return self.__str__()
        
class TaspHeaderOptions:
    Mode:int
    Cols:list[str]|None
    Direction:int
    Schema:list[LanType|int]|None
    ColKey:int|None
    RowKey:int|None
    KeysRow:int|None
    
    type RawOptionsList = list[tuple[str,str|None]]
    
    def __init__(self, opts:RawOptionsList):
        self.Mode = 0
        # MODES:
        # 0 : List, all data is a linear, straight array of values. [1, 2, 3, 4, 5, 6]
        # 1 : Double list, returns a list of lists. [[1,2,3],[4,5,6]]
        # 2 : Simple Object, an object with keys and values, values being lists of the columns. (name=>[1,2,3], other=>[4,5,6])
        # 3 : Complex List, a list of simple object, with key/values pairs. [(name=>anthony, age=>18),(name=>zach, age=>19)]
        # 4 : Complex Object, an object with keys and values which are also key/value objects. (anthony=>(age=>18),zach=>(age=>19))
        self.Direction = 0
        # DIRECTION:
        # 0 : Columns, the data is interpreted top-down (default)
        # 1 : Rows, the data is interpreted left-right
        self.Schema = None
        # SCHEMA:
        # Dictates how the columns (or rows, in dir=1) should be cast into values.
        self.ColKey = None
        self.RowKey = None
        self.KeysRow = None
        self.Init(opts)
    
    ModeOptions = [
        ["0", "list"],
        ["1", "double-list", "d-list"],
        ["2", "object", "obj"],
        ["3", "complex-list", "cx-list"],
        ["4", "complex-object", "cx-obj"]
    ]
    
    @classmethod
    def _interpret_mode(cls, string:str) -> int:
        for i, mode_opts in enumerate(cls.ModeOptions):
            if string in mode_opts: return i
        raise Exception("The value provided does not match anything!")
    
    def Init(self, opts:RawOptionsList) -> None:
        
        for opt in opts:
            # Single declartion cases
            if opt[1] is None: pass
            # Double declaration cases
            else:
                match opt[0]:
                    case 'mode': self.Mode = self._interpret_mode(opt[1])
                    case 'schema':
                        self.Schema = []
                        structs = CodeCleaner.split_top_level_commas(opt[1])
                        for i, struct in enumerate(structs):
                            if struct.strip() == "<key>":
                                if self.Mode not in [2,4]: raise Exception("Should not be defining <key> for non-complex objects.")
                                self.RowKey = i
                                self.Schema.append(-1)
                            else:
                                self.Schema.append(LanType.get_type_from_typestr(struct.strip()))
                    case 'keys-row':
                        if self.Mode not in [2,3,4]: raise Exception(f"Should not be defining keys-row for this mode: {self.Mode}")
                        self.KeysRow=int(opt[1])
                    
    def __repr__(self) -> str:
        lines = [
            f"Mode: {self.ModeOptions[self.Mode][1]}",
            f"Direction: {("Column" if self.Direction == 0 else "Row")}",
            f"Schema: {(", ".join([("<Key> " if i == self.RowKey else "") + str(item) for i, item in enumerate (self.Schema or [])]))}",
            f"Keys-Row: {self.KeysRow}",
            f"Row-Key: {self.RowKey}",
            f"Column-Key: {self.ColKey}"
        ]
        return "[Header Options]\n"*AnsiColor.CYAN + "\n".join(lines) + "\n[--------------]"*AnsiColor.CYAN
        

# Notes
# TASP, or tablespeak, is a simple or complex object definition language.
# It takes both elements from CSV and JSON, and can be used, and should be,
# in Myriware Mylange.

### DEBUG ###

if __name__ == "__main__":
    tasp = TableSpeak()
    tasp.InterpretFile(sys.argv[1])
    print(tasp)