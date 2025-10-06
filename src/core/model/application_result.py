from typing import Optional, TypedDict


class ApplicationResult(TypedDict):
    id_job: int
    success: bool
    error: Optional[str]
