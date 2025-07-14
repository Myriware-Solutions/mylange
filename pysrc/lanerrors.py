

class LanErrors:

    class StopProgramExecution(Exception):
        def __init__(this, msg="Used to safely stop due to an unrecoverable error.", value=None):
            this.value = value
            this.message = msg
            super().__init__(this.message)

    class MemoryMissingError(Exception):
        def __init__(this, msg="Could not find variable by name", value=None):
            this.value = value
            this.message = msg
            super().__init__(this.message)