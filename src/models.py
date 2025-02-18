from enum import Enum
from dataclasses import dataclass
from typing import Optional, Any

class ResponseStatus(Enum):
    SUCCESS = "success"
    ERROR = "error"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ApiResponse:
    status: ResponseStatus
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

    def to_dict(self):
        return {
            "status": self.status.value,
            "message": self.message,
            "data": self.data,
            "error": self.error
        } 