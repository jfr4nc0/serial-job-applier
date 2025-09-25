# LinkedIn Job Application Automation System

A comprehensive AI-powered system for automating LinkedIn job applications using FastMCP, LangGraph, and intelligent form filling.

## Architecture

The system uses the **official MCP SDK** with stdio transport for proper protocol compliance:

### Core Job Application Agent (`core-agent` container)
- **MCP Client**: Uses official `mcp` SDK with stdio transport for protocol communication
- **MCP Server**: LinkedIn server runs as subprocess via stdio (not HTTP)
- **LangGraph Workflow**: Orchestrates the complete job application process
- **CV Analysis**: AI-powered PDF CV reading and structured data extraction
- **Job Filtering**: Intelligent job matching based on CV profile alignment
- **RPA Automation**: Selenium-based LinkedIn interaction with anti-detection
- **AI Form Filling**: Uses Qwen2.5-32B model for intelligent form completion

## Features

 **AI-Powered CV Analysis**: Extracts skills, experience, education from PDF CVs
 **Intelligent Job Search**: Multi-criteria LinkedIn job searching with pagination
 **Smart Job Filtering**: AI-based job relevance scoring using CV profile
 **Advanced Form Filling**: AI handles dynamic LinkedIn application forms
 **Anti-Detection RPA**: Randomized delays and user-agent rotation
 **Containerized Architecture**: Scalable Docker-based deployment
 **Error Handling**: Comprehensive error recovery and logging

## Quick Start

### Prerequisites
- Docker and Docker Compose
- LinkedIn account credentials
- PDF CV file

### 1. Clone and Setup
```bash
git clone <repository-url>
cd serial-job-applier
```

### 2. Environment Configuration
Create `.env` file:
```bash
LINKEDIN_EMAIL=your-email@example.com
LINKEDIN_PASSWORD=your-password
CV_FILE_PATH=/app/data/cv.pdf
MCP_SERVER_URL=http://linkedin-mcp:8000
```

### 3. Prepare CV File
```bash
mkdir -p data
cp /path/to/your/cv.pdf data/cv.pdf
```

### 4. Start the System
```bash
# Build and start the agent
docker-compose up -d

# Check logs
docker-compose logs -f core-agent
```

### 5. The job application workflow runs automatically when the container starts

## System Components

### MCP Tools
- **`search_jobs`**: LinkedIn job search with Easy Apply filtering
- **`easy_apply_for_jobs`**: AI-powered job application with form filling

### Core Services
- **`JobApplicationAgent`**: Main orchestration agent with LangGraph workflow
- **`LinkedInMCPClient`**: HTTP client for MCP protocol communication
- **`EasyApplyAgent`**: AI form analysis and filling agent
- **`BrowserManager`**: Selenium automation with anti-detection

### AI Models
- **Qwen2.5-32B**: Used for CV analysis and form question answering
- **PDF Processing**: PyPDF2 and pdfplumber for CV text extraction

## Workflow

1. **CV Analysis**: Extract and structure data from PDF CV
2. **Job Search**: Multi-criteria LinkedIn search via MCP protocol
3. **Job Filtering**: AI-powered relevance scoring based on CV profile
4. **Application**: Intelligent form filling for each selected job
5. **Results**: Comprehensive reporting of application outcomes

## Dependencies

- **Core**: Python 3.12, LangGraph, LangChain, FastMCP
- **RPA**: Selenium, undetected-chromedriver, BeautifulSoup4
- **AI**: ChatOllama (Qwen2.5-32B model)
- **PDF**: PyPDF2, pdfplumber
- **HTTP**: httpx, requests

## License

This project is for educational and research purposes. Ensure compliance with LinkedIn's Terms of Service and applicable laws when using automated tools.
