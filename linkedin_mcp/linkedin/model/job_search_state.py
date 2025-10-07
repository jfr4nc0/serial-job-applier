from typing import List, Optional, TypedDict

from linkedin_mcp.linkedin.interfaces.services import IBrowserManager
from linkedin_mcp.linkedin.model.types import JobResult


class JobSearchState(TypedDict):
    job_title: str
    location: str
    easy_apply: bool
    limit: int
    browser_manager: IBrowserManager
    current_page: int
    collected_jobs: List[JobResult]
    search_url: Optional[str]
    total_found: int
    errors: List[str]
