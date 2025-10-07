"""
Interface definitions for LinkedIn MCP components.
Following SOLID principles to enable dependency inversion.
"""

from linkedin_mcp.linkedin.interfaces.agents import IJobApplicationAgent
from linkedin_mcp.linkedin.interfaces.services import (
    IBrowserManager,
    IJobApplicationService,
    IJobSearchService,
)

__all__ = [
    "IJobApplicationAgent",
    "IBrowserManager",
    "IJobApplicationService",
    "IJobSearchService",
]
