from typing import Any, Dict, List, Optional, TypedDict


class JobSearchRequest(TypedDict):
    job_title: str
    location: str
    monthly_salary: int
    limit: int


class JobResult(TypedDict):
    id_job: int
    job_description: str


class ApplicationRequest(TypedDict):
    job_id: int
    monthly_salary: int


class ApplicationResult(TypedDict):
    id_job: int
    success: bool
    error: Optional[str]


class CVAnalysis(TypedDict):
    skills: List[str]
    experience_years: int
    previous_roles: List[str]
    education: List[str]
    certifications: List[str]
    domains: List[str]
    key_achievements: List[str]
    technologies: List[str]


class JobApplicationAgentState(TypedDict):
    # Input from user
    job_searches: List[JobSearchRequest]
    cv_file_path: str
    cv_content: str
    user_credentials: Dict[str, str]  # {email, password}

    # Processing state
    current_search_index: int
    all_found_jobs: List[JobResult]
    filtered_jobs: List[JobResult]
    application_results: List[ApplicationResult]

    # Agent memory
    cv_analysis: CVAnalysis
    conversation_history: List[Dict[str, Any]]
    errors: List[str]

    # Status tracking
    total_jobs_found: int
    total_jobs_applied: int
    current_status: str
