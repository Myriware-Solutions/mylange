class LanErrors:

    class MylangeError(Exception):
        message:str
        value:None
        
    class ErrorWrapper(Exception):
        line:str
        error:Exception
        def __init__(self, line:str, error:Exception) -> None:
            self.line = line
            self.error = error
            super().__init__()

    # Used as Program indicators, not errors
    class StopProgramExecution(MylangeError):
        def __init__(self, msg="Used to safely stop due to an unrecoverable error.", value=None):
            self.value = value
            self.message = msg
            super().__init__(self.message)

    class Break(MylangeError):
        def __init__(self, msg="Used to break loops.", value=None):
            self.value = value
            self.message = msg
            super().__init__(self.message)

    class Continue(MylangeError):
        def __init__(self, msg="Used to continue loops.", value=None):
            self.value = value
            self.message = msg
            super().__init__(self.message)

    # Legit Errors
    class MemoryMissingError(MylangeError):
        def __init__(self, msg="MemoryMissingError-undefined_error_info", value=None):
            self.value = value
            self.message = f"Could not find variable by name: '{msg}'"
            super().__init__(self.message)

    class NotIndexableError(MylangeError):
        def __init__(self, msg="Cannot Index non-indexable variable.", value=None):
            self.value = value
            self.message = msg
            super().__init__(self.message)

    class ConditionalNotBoolError(MylangeError):
        def __init__(self, msg="Cannot use self for boolean logic.", value=None):
            self.value = value
            self.message = msg
            super().__init__(self.message)
    
    class WrongTypeExpectationError(MylangeError):
        def __init__(self, msg="Trying to set something to a different type.", value=None):
            self.value = value
            self.message = msg
            super().__init__(self.message)

    class CannotFindQuerryError(MylangeError):
        def __init__(self, msg="Cannot figure out what self input is:", value=None):
            self.value = value
            self.message = msg
            super().__init__(self.message)

    class MissingImportError(MylangeError):
        def __init__(self, msg="Cannot find thing to import", value=None):
            self.value = value
            self.message = msg
            super().__init__(self.message)
    
    class DuplicateMethodError(MylangeError):
        def __init__(self, msg="DuplicateMethodError-undefined_error_info", value=None):
            self.value = value
            self.message = f"Trying to create another method with the same name: {msg}"
            super().__init__(self.message)
    
    class DuplicatePropertyError(MylangeError):
        def __init__(self, msg="DuplicatePropertyError-undefined_error_info", value=None):
            self.value = value
            self.message = f"Trying to create another property with the same name: {msg}"
            super().__init__(self.message)
            
    class UnknownTypeError(MylangeError):
        def __init__(self, msg:str="UnknownTypeError-undefined_error_info", value=None) -> None:
            self.value = value
            self.message = f"Unknown or undefined type used: {msg}"
            super().__init__(self.message)
            
    class MissingIndexError(MylangeError):
        def __init__(self, msg:str="MissingIndexError-undefined_error_info", value=None) -> None:
            self.message = f"Could not retrive the index on object for: {msg}"
            self.value = value
            super().__init__(self.message)