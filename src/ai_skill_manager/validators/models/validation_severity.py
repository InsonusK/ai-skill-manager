from enum import Enum


class ValidationSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    SUCCESS = "success"