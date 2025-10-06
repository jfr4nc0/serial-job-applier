from typing import List, TypedDict


class CVAnalysis(TypedDict):
    skills: List[str]
    experience_years: int
    previous_roles: List[str]
    education: List[str]
    certifications: List[str]
    domains: List[str]
    key_achievements: List[str]
    technologies: List[str]
