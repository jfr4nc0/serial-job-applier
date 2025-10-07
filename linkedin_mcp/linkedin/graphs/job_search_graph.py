# Re-export classes for backward compatibility
from linkedin_mcp.linkedin.graphs.job_search_graph_impl import JobSearchGraph
from linkedin_mcp.linkedin.model.job_search_state import JobSearchState

__all__ = ["JobSearchState", "JobSearchGraph"]
