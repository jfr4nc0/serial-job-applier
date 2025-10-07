#!/usr/bin/env python3
"""
LinkedIn Job Application Agent - Terminal Client
Entry point for the command-line interface.
"""

from cli.client import JobApplicationCLI


def main():
    """Main entry point for the CLI application."""
    cli = JobApplicationCLI()
    cli.run()


if __name__ == "__main__":
    main()
