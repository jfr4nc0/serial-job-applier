from typing import List, Optional, TypedDict

from linkedin_mcp.linkedin.services.browser_manager_service import (
    BrowserManagerService as BrowserManager,
)
from linkedin_mcp.types import JobResult


class JobSearchState(TypedDict):
    job_title: str
    location: str
    easy_apply: bool
    limit: int
    browser_manager: BrowserManager
    current_page: int
    collected_jobs: List[JobResult]
    search_url: Optional[str]
    total_found: int
    errors: List[str]
