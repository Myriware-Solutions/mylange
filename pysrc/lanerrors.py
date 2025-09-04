class LanErrors:

    class MylangeError(Exception):
        pass

    # Used as Program indicators, not errors
    class StopProgramExecution(MylangeError):
        def __init__(this, msg="Used to safely stop due to an unrecoverable error.", value=None):
            this.value = value
            this.message = msg
            super().__init__(this.message)

    class Break(MylangeError):
        def __init__(this, msg="Used to break loops.", value=None):
            this.value = value
            this.message = msg
            super().__init__(this.message)

    class Continue(MylangeError):
        def __init__(this, msg="Used to continue loops.", value=None):
            this.value = value
            this.message = msg
            super().__init__(this.message)

    # Legit Errors
    class MemoryMissingError(MylangeError):
        def __init__(this, msg="Could not find variable by name.", value=None):
            this.value = value
            this.message = msg
            super().__init__(this.message)

    class NotIndexableError(MylangeError):
        def __init__(this, msg="Cannot Index non-indexable variable.", value=None):
            this.value = value
            this.message = msg
            super().__init__(this.message)

    class ConditionalNotBoolError(MylangeError):
        def __init__(this, msg="Cannot use this for boolean logic.", value=None):
            this.value = value
            this.message = msg
            super().__init__(this.message)
    
    class WrongTypeExpectationError(MylangeError):
        def __init__(this, msg="Trying to set something to a different type.", value=None):
            this.value = value
            this.message = msg
            super().__init__(this.message)

    class CannotFindQuerryError(MylangeError):
        def __init__(this, msg="Cannot figure out what this input is:", value=None):
            this.value = value
            this.message = msg
            super().__init__(this.message)

    class MissingImportError(MylangeError):
        def __init__(this, msg="Cannot find thing to import", value=None):
            this.value = value
            this.message = msg
            super().__init__(this.message)
    
    class DuplicateMethodError(MylangeError):
        def __init__(this, msg="DuplicateMethodError-undefined_error_info", value=None):
            this.value = value
            this.message = f"Trying to create another method with the same name: {msg}"
            super().__init__(this.message)
    
    class DuplicatePropertyError(MylangeError):
        def __init__(this, msg="DuplicatePropertyError-undefined_error_info", value=None):
            this.value = value
            this.message = f"Trying to create another property with the same name: {msg}"
            super().__init__(this.message)