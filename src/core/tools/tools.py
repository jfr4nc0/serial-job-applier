import os
import re

import pdfplumber
import PyPDF2
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool

from src.core.model.cv_analysis import CVAnalysis
from src.core.providers.llm_client import get_llm_client


@tool
def read_pdf_cv(file_path: str) -> str:
    """
    Extract text content from PDF CV file.

    Args:
        file_path: Path to the PDF CV file

    Returns:
        Extracted text content from the PDF
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"CV file not found at: {file_path}")

    if not file_path.lower().endswith(".pdf"):
        raise ValueError("File must be a PDF")

    try:
        # Try pdfplumber first (better text extraction)
        with pdfplumber.open(file_path) as pdf:
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\\n\\n"

            if text.strip():
                return text.strip()

    except Exception as e:
        print(f"pdfplumber failed: {e}, trying PyPDF2...")

    try:
        # Fallback to PyPDF2
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""

            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\\n\\n"

            return text.strip()

    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


@tool
def analyze_cv_structure(cv_text: str) -> CVAnalysis:
    """
    Use AI to extract structured data from CV text.

    Args:
        cv_text: Raw text content from CV

    Returns:
        Structured CV analysis data
    """
    # Initialize the VLLM model
    model = get_llm_client()

    # Create analysis prompt
    prompt = ChatPromptTemplate.from_template(
        """
    Analyze the following CV text and extract structured information.

    CV Content:
    {cv_text}

    Extract and return ONLY a JSON object with these fields:
    {{
        "skills": ["list of technical skills"],
        "experience_years": number_of_years_experience,
        "previous_roles": ["list of job titles/positions"],
        "education": ["degrees, universities, relevant education"],
        "certifications": ["professional certifications"],
        "domains": ["industry domains/sectors worked in"],
        "key_achievements": ["notable achievements or projects"],
        "technologies": ["programming languages, frameworks, tools"]
    }}

    Be specific and comprehensive. Extract only factual information present in the CV.
    """
    )

    try:
        # Get AI analysis
        chain = prompt | model
        response = chain.invoke({"cv_text": cv_text})

        # Parse the response (assuming it returns structured data)
        import json

        # Clean the response text to extract JSON
        response_text = (
            response.content if hasattr(response, "content") else str(response)
        )

        # Try to extract JSON from the response
        json_match = re.search(r"\\{.*\\}", response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
            analysis_data = json.loads(json_str)
        else:
            # Fallback parsing
            analysis_data = json.loads(response_text)

        # Ensure all required fields exist
        cv_analysis = CVAnalysis(
            skills=analysis_data.get("skills", []),
            experience_years=analysis_data.get("experience_years", 0),
            previous_roles=analysis_data.get("previous_roles", []),
            education=analysis_data.get("education", []),
            certifications=analysis_data.get("certifications", []),
            domains=analysis_data.get("domains", []),
            key_achievements=analysis_data.get("key_achievements", []),
            technologies=analysis_data.get("technologies", []),
        )

        return cv_analysis

    except Exception as e:
        print(f"Error analyzing CV with AI: {e}")
        # Return basic fallback analysis
        return CVAnalysis(
            skills=_extract_basic_skills(cv_text),
            experience_years=_extract_basic_experience(cv_text),
            previous_roles=_extract_basic_roles(cv_text),
            education=[],
            certifications=[],
            domains=[],
            key_achievements=[],
            technologies=[],
        )


def _extract_basic_skills(text: str) -> list:
    """Fallback basic skill extraction using regex"""
    common_skills = [
        "python",
        "javascript",
        "java",
        "react",
        "django",
        "flask",
        "sql",
        "postgresql",
        "mysql",
        "mongodb",
        "docker",
        "kubernetes",
        "aws",
        "azure",
        "gcp",
        "machine learning",
        "deep learning",
        "tensorflow",
        "pytorch",
        "pandas",
        "numpy",
        "scikit-learn",
    ]

    found_skills = []
    text_lower = text.lower()

    for skill in common_skills:
        if skill in text_lower:
            found_skills.append(skill.title())

    return found_skills


def _extract_basic_experience(text: str) -> int:
    """Fallback basic experience extraction using regex"""
    # Look for patterns like "5 years", "3+ years", etc.
    experience_patterns = [
        r"(\\d+)\\s*\\+?\\s*years?\\s+(?:of\\s+)?experience",
        r"(\\d+)\\s*years?\\s+(?:of\\s+)?(?:professional\\s+)?experience",
        r"experience\\s*:?\\s*(\\d+)\\s*years?",
    ]

    for pattern in experience_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return int(matches[0])

    return 0


def _extract_basic_roles(text: str) -> list:
    """Fallback basic role extraction"""
    common_roles = [
        "software engineer",
        "developer",
        "data scientist",
        "analyst",
        "manager",
        "senior",
        "junior",
        "lead",
        "architect",
        "consultant",
    ]

    found_roles = []
    text_lower = text.lower()

    for role in common_roles:
        if role in text_lower:
            found_roles.append(role.title())

    return list(set(found_roles))  # Remove duplicates
