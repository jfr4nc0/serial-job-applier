"""Rich terminal UI components for the CLI client."""

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table
from rich.text import Text
from rich.tree import Tree


class TerminalUI:
    """Rich terminal UI for the job application workflow."""

    def __init__(self, output_format: str = "rich"):
        self.console = Console()
        self.output_format = output_format
        self.start_time = None

    def print_header(self):
        """Print application header."""
        if self.output_format != "rich":
            return

        header_text = Text("LinkedIn Job Application Agent", style="bold blue")
        header_text.append(" 🤖", style="bold yellow")

        panel = Panel(
            header_text,
            subtitle="Automated job search and application system",
            border_style="blue",
        )
        self.console.print(panel)
        self.console.print()

    def print_config_summary(self, config):
        """Print configuration summary."""
        if self.output_format == "json":
            return

        table = Table(
            title="Configuration Summary", show_header=True, header_style="bold magenta"
        )
        table.add_column("Setting", style="cyan")
        table.add_column("Value", style="green")

        table.add_row(
            "MCP Server", f"{config.mcp_server_host}:{config.mcp_server_port}"
        )
        table.add_row("CV Data", config.cv_file_path)
        table.add_row("LinkedIn Email", config.linkedin_email)
        table.add_row("Job Searches", str(len(config.job_searches)))

        if self.output_format == "rich":
            self.console.print(table)
        else:
            # Simple format
            self.console.print("Configuration:")
            self.console.print(
                f"  MCP Server: {config.mcp_server_host}:{config.mcp_server_port}"
            )
            self.console.print(f"  CV File: {config.cv_file_path}")
            self.console.print(f"  Job Searches: {len(config.job_searches)}")

        self.console.print()

    def print_job_searches(self, job_searches: List[Dict]):
        """Print job search configurations."""
        if self.output_format == "json":
            return

        table = Table(
            title="Job Search Criteria", show_header=True, header_style="bold magenta"
        )
        table.add_column("Job Title", style="cyan")
        table.add_column("Location", style="green")
        table.add_column("Salary", style="yellow")
        table.add_column("Limit", style="blue")

        for search in job_searches:
            table.add_row(
                search.job_title,
                search.location,
                f"${search.monthly_salary:,}/month",
                str(search.limit),
            )

        if self.output_format == "rich":
            self.console.print(table)
        else:
            self.console.print("Job Search Criteria:")
            for i, search in enumerate(job_searches, 1):
                self.console.print(
                    f"  {i}. {search.job_title} in {search.location} (${search.monthly_salary:,}/month, limit: {search.limit})"
                )

        self.console.print()

    def create_progress_display(self) -> Progress:
        """Create a progress display for the workflow."""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console,
            transient=False,
        )

    def show_workflow_progress(self, agent_state: Dict[str, Any]):
        """Show live workflow progress."""
        if self.output_format != "rich":
            # Simple text output
            self.console.print(
                f"Status: {agent_state.get('current_status', 'Unknown')}"
            )
            return

        # Create layout
        layout = Layout()
        layout.split_column(
            Layout(name="status", size=3),
            Layout(name="details"),
        )

        # Status panel
        status = agent_state.get("current_status", "Starting...")
        status_panel = Panel(
            Text(status, style="bold green"),
            title="Current Status",
            border_style="green",
        )
        layout["status"].update(status_panel)

        # Details panel
        details_text = Text()

        if agent_state.get("total_jobs_found"):
            details_text.append(
                f"📍 Jobs Found: {agent_state['total_jobs_found']}\n", style="blue"
            )

        if agent_state.get("filtered_jobs"):
            details_text.append(
                f"✅ Jobs Filtered: {len(agent_state['filtered_jobs'])}\n",
                style="green",
            )

        if agent_state.get("total_jobs_applied"):
            details_text.append(
                f"🎯 Applications Submitted: {agent_state['total_jobs_applied']}\n",
                style="yellow",
            )

        if agent_state.get("errors"):
            details_text.append(
                f"❌ Errors: {len(agent_state['errors'])}\n", style="red"
            )

        details_panel = Panel(
            details_text, title="Progress Details", border_style="blue"
        )
        layout["details"].update(details_panel)

        self.console.print(layout)

    def print_cv_analysis(self, cv_analysis: Dict[str, Any]):
        """Print CV analysis results."""
        if self.output_format == "json":
            print(json.dumps({"cv_analysis": cv_analysis}, indent=2))
            return

        tree = Tree("📄 CV Analysis", style="bold blue")

        # Experience
        exp_branch = tree.add("💼 Experience", style="green")
        exp_branch.add(f"Years: {cv_analysis.get('experience_years', 0)}")

        # Skills
        skills_branch = tree.add("🛠️  Skills", style="cyan")
        skills = cv_analysis.get("skills", [])
        for skill in skills[:10]:  # Show first 10 skills
            skills_branch.add(skill)
        if len(skills) > 10:
            skills_branch.add(f"... and {len(skills) - 10} more")

        # Previous roles
        roles_branch = tree.add("👔 Previous Roles", style="yellow")
        roles = cv_analysis.get("previous_roles", [])
        for role in roles[:5]:  # Show first 5 roles
            roles_branch.add(role)
        if len(roles) > 5:
            roles_branch.add(f"... and {len(roles) - 5} more")

        # Technologies
        tech_branch = tree.add("💻 Technologies", style="magenta")
        technologies = cv_analysis.get("technologies", [])
        for tech in technologies[:8]:  # Show first 8 technologies
            tech_branch.add(tech)
        if len(technologies) > 8:
            tech_branch.add(f"... and {len(technologies) - 8} more")

        if self.output_format == "rich":
            self.console.print(tree)
        else:
            self.console.print("CV Analysis:")
            self.console.print(
                f"  Experience: {cv_analysis.get('experience_years', 0)} years"
            )
            self.console.print(
                f"  Skills: {', '.join(skills[:5])}{'...' if len(skills) > 5 else ''}"
            )
            self.console.print(
                f"  Previous Roles: {', '.join(roles[:3])}{'...' if len(roles) > 3 else ''}"
            )

        self.console.print()

    def print_job_results(self, jobs: List[Dict[str, Any]]):
        """Print job search results."""
        if self.output_format == "json":
            print(json.dumps({"jobs_found": jobs}, indent=2))
            return

        if not jobs:
            self.console.print("❌ No jobs found", style="red")
            return

        table = Table(
            title=f"Found {len(jobs)} Jobs",
            show_header=True,
            header_style="bold magenta",
        )
        table.add_column("Job ID", style="cyan")
        table.add_column("Description Preview", style="green", max_width=60)

        for job in jobs:
            description_preview = (
                job.get("job_description", "")[:100] + "..."
                if len(job.get("job_description", "")) > 100
                else job.get("job_description", "")
            )
            table.add_row(str(job.get("id_job", "N/A")), description_preview)

        if self.output_format == "rich":
            self.console.print(table)
        else:
            self.console.print(f"Found {len(jobs)} jobs:")
            for i, job in enumerate(jobs, 1):
                description_preview = (
                    job.get("job_description", "")[:50] + "..."
                    if len(job.get("job_description", "")) > 50
                    else job.get("job_description", "")
                )
                self.console.print(
                    f"  {i}. Job {job.get('id_job')}: {description_preview}"
                )

        self.console.print()

    def print_application_results(self, application_results: List[Dict[str, Any]]):
        """Print job application results."""
        if self.output_format == "json":
            print(json.dumps({"application_results": application_results}, indent=2))
            return

        if not application_results:
            self.console.print("❌ No applications submitted", style="red")
            return

        table = Table(
            title="Application Results", show_header=True, header_style="bold magenta"
        )
        table.add_column("Job ID", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Error", style="red")

        successful = 0
        for result in application_results:
            status = "✅ SUCCESS" if result.get("success") else "❌ FAILED"
            error = result.get("error", "") if not result.get("success") else ""

            table.add_row(
                str(result.get("id_job", "N/A")),
                status,
                error[:50] + "..." if len(error) > 50 else error,
            )

            if result.get("success"):
                successful += 1

        if self.output_format == "rich":
            self.console.print(table)
        else:
            self.console.print(
                f"Application Results ({successful}/{len(application_results)} successful):"
            )
            for result in application_results:
                status = "SUCCESS" if result.get("success") else "FAILED"
                self.console.print(f"  Job {result.get('id_job')}: {status}")
                if not result.get("success") and result.get("error"):
                    self.console.print(f"    Error: {result['error'][:100]}")

        self.console.print()

    def print_final_summary(self, final_state: Dict[str, Any]):
        """Print final workflow summary."""
        if self.output_format == "json":
            # Clean up the state for JSON output
            clean_state = {
                k: v for k, v in final_state.items() if k not in ["cv_content"]
            }
            print(json.dumps(clean_state, indent=2, default=str))
            return

        # Calculate execution time
        elapsed_time = ""
        if self.start_time:
            elapsed = time.time() - self.start_time
            elapsed_time = f" (Completed in {elapsed:.1f}s)"

        panel_title = f"🎉 Workflow Complete{elapsed_time}"

        summary_text = Text()
        summary_text.append("📊 Summary:\n", style="bold blue")
        summary_text.append(
            f"  • Jobs Found: {final_state.get('total_jobs_found', 0)}\n", style="green"
        )
        summary_text.append(
            f"  • Jobs Filtered: {len(final_state.get('filtered_jobs', []))}\n",
            style="yellow",
        )
        summary_text.append(
            f"  • Applications Submitted: {final_state.get('total_jobs_applied', 0)}\n",
            style="cyan",
        )

        if final_state.get("errors"):
            summary_text.append(
                f"  • Errors: {len(final_state['errors'])}\n", style="red"
            )

        summary_text.append(
            f"\n✅ Status: {final_state.get('current_status', 'Complete')}",
            style="bold green",
        )

        panel = Panel(summary_text, title=panel_title, border_style="green")

        if self.output_format == "rich":
            self.console.print(panel)
        else:
            self.console.print(f"Workflow Complete{elapsed_time}")
            self.console.print(f"Jobs Found: {final_state.get('total_jobs_found', 0)}")
            self.console.print(
                f"Jobs Filtered: {len(final_state.get('filtered_jobs', []))}"
            )
            self.console.print(
                f"Applications Submitted: {final_state.get('total_jobs_applied', 0)}"
            )
            if final_state.get("errors"):
                self.console.print(f"Errors: {len(final_state['errors'])}")

    def print_errors(self, errors: List[str]):
        """Print errors encountered during execution."""
        if not errors:
            return

        if self.output_format == "json":
            print(json.dumps({"errors": errors}, indent=2))
            return

        self.console.print("\n❌ Errors encountered:", style="bold red")
        for i, error in enumerate(errors, 1):
            if self.output_format == "rich":
                self.console.print(f"  {i}. {error}", style="red")
            else:
                self.console.print(f"  {i}. {error}")

    def start_timer(self):
        """Start timing the workflow."""
        self.start_time = time.time()

    def prompt_user_input(self, message: str, default: Optional[str] = None) -> str:
        """Prompt user for input."""
        if default:
            prompt = f"{message} [{default}]: "
        else:
            prompt = f"{message}: "

        return self.console.input(prompt) or default
