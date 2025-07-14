

class LanErrors:

    class MylangeError(Exception):
        pass

    class StopProgramExecution(MylangeError):
        def __init__(this, msg="Used to safely stop due to an unrecoverable error.", value=None):
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