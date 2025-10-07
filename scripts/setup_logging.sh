#!/bin/bash
"""
Setup script for LinkedIn Job Application Agent logging infrastructure.
Creates log directories and sets appropriate permissions.
"""

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Setting up LinkedIn Job Application Agent logging infrastructure...${NC}"

# Create logs directory structure
echo -e "${YELLOW}📁 Creating log directories...${NC}"
mkdir -p logs
mkdir -p logs/archive

# Create log files with proper permissions
echo -e "${YELLOW}📝 Creating log files...${NC}"
touch logs/job_applier.log
touch logs/core_agent.log
touch logs/linkedin_mcp.log

# Set permissions (optional - adjust as needed)
chmod 644 logs/*.log

echo -e "${GREEN}✅ Log directories and files created successfully!${NC}"

# Display directory structure
echo -e "${BLUE}📂 Logging structure:${NC}"
tree logs/ 2>/dev/null || ls -la logs/

echo ""
echo -e "${BLUE}📝 Log file descriptions:${NC}"
echo -e "  ${GREEN}logs/job_applier.log${NC}     - General application logs"
echo -e "  ${GREEN}logs/core_agent.log${NC}      - Core agent workflow logs"
echo -e "  ${GREEN}logs/linkedin_mcp.log${NC}    - LinkedIn MCP server logs"
echo -e "  ${GREEN}logs/archive/${NC}            - Archived/rotated logs"

echo ""
echo -e "${BLUE}🔧 Environment configuration:${NC}"
echo -e "Add these to your ${GREEN}.env${NC} file for logging:"
echo ""
echo "# Core Agent Logging"
echo "CORE_AGENT_LOG_LEVEL=INFO"
echo "CORE_AGENT_LOG_FILE=./logs/core_agent.log"
echo ""
echo "# LinkedIn MCP Server Logging"
echo "LINKEDIN_MCP_LOG_LEVEL=INFO"
echo "LINKEDIN_MCP_LOG_FILE=./logs/linkedin_mcp.log"
echo ""
echo "# General Logging"
echo "LOG_LEVEL=INFO"
echo "LOG_FILE=./logs/job_applier.log"

echo ""
echo -e "${BLUE}🔍 Monitoring logs:${NC}"
echo -e "  ${YELLOW}# Watch all logs in real-time${NC}"
echo -e "  tail -f logs/*.log"
echo ""
echo -e "  ${YELLOW}# Filter by trace ID${NC}"
echo -e "  grep 'trace_id=abc123' logs/core_agent.log"
echo ""
echo -e "  ${YELLOW}# View errors only${NC}"
echo -e "  grep 'ERROR' logs/*.log"

echo ""
echo -e "${GREEN}🎉 Logging setup completed!${NC}"
echo -e "Run ${YELLOW}python -m cli.client run${NC} to start with structured logging."
