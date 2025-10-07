from typing import Any, List, Optional, TypedDict


class CVAnalysis(TypedDict):
    skills: List[str]
    experience_years: int
    previous_roles: List[str]
    education: List[str]
    certifications: List[str]
    domains: List[str]
    key_achievements: List[str]
    technologies: List[str]


class ApplicationRequest(TypedDict):
    job_id: int
    monthly_salary: int


class ApplicationResult(TypedDict):
    id_job: int
    success: bool
    error: Optional[str]


class JobResult(TypedDict):
    job_id: str
    title: str
    company: str
    location: str
    description: str
    easy_apply: bool


class AuthState(TypedDict):
    email: str
    password: str
    browser_manager: Any
    authenticated: bool
