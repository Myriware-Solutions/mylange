

class LanErrors:

    class MylangeError(Exception):
        pass

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