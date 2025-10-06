# LinkedIn Job Application Automation System

A comprehensive AI-powered system for automating LinkedIn job applications using FastMCP, LangGraph, and intelligent form filling.

## Architecture

The system uses a **single-container architecture** with Hugging Face Serverless API for cloud-based AI inference:

### Core Job Application Agent (`core-agent` container)
- **MCP Client**: Uses official `mcp` SDK with stdio transport for protocol communication
- **MCP Server**: LinkedIn server runs as subprocess via stdio (not HTTP)
- **LangGraph Workflow**: Orchestrates the complete job application process
- **CV Analysis**: AI-powered PDF CV reading and structured data extraction
- **Job Filtering**: Intelligent job matching based on CV profile alignment
- **RPA Automation**: Selenium-based LinkedIn interaction with anti-detection
- **AI Form Filling**: Uses Hugging Face Serverless API for intelligent form completion

### AI Inference
- **Hugging Face Serverless API**: Cloud-based inference with Qwen3-30B-A3B-Thinking
- **No GPU Required**: Serverless inference eliminates infrastructure complexity
- **Scalable**: Automatic scaling and high availability
- **Cost Effective**: Pay-per-use pricing model

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
- Hugging Face account and API token (for serverless inference)

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
HUGGING_FACE_HUB_TOKEN=your-hf-token-here
```

### 3. Prepare CV File
```bash
mkdir -p data
cp /path/to/your/cv.pdf data/cv.pdf
```

### 4. Start the System
```bash
# Build and start the core agent
docker-compose up -d

# Check core agent logs
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
- **Qwen3-30B-A3B-Thinking**: Advanced reasoning model via Hugging Face Serverless API
- **Serverless Inference**: Cloud-based high-performance inference
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
- **AI**: Hugging Face Serverless API (Qwen3-30B-A3B-Thinking), LangChain-HuggingFace
- **PDF**: PyPDF2, pdfplumber
- **Infrastructure**: Docker

## License

This project is for educational and research purposes. Ensure compliance with LinkedIn's Terms of Service and applicable laws when using automated tools.
