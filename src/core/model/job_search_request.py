from typing import TypedDict


class JobSearchRequest(TypedDict):
    job_title: str
    location: str
    monthly_salary: int
    limit: int
