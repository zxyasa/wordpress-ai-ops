class TaskValidationError(Exception):
    pass


class SafetyViolationError(Exception):
    pass


class TargetNotFoundError(Exception):
    pass


class WPClientError(Exception):
    pass
