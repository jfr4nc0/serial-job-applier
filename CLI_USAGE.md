# LinkedIn Job Application Agent - CLI Usage Guide

The terminal client provides a comprehensive command-line interface for the LinkedIn Job Application Agent, offering both interactive and automated workflows.

## Quick Start

### 1. Basic Usage with Environment Variables

```bash
# Set required environment variables
export LINKEDIN_EMAIL="your-email@example.com"
export LINKEDIN_PASSWORD="your-password"
export CV_FILE_PATH="./data/cv.pdf"

# Run with interactive job search setup
python job_applier.py run --interactive

# Or run with default configuration
python job_applier.py run
```

### 2. Using Configuration Files

```bash
# Initialize a configuration file
python job_applier.py init --config ./my-config.yaml

# Run with configuration file
python job_applier.py run --config ./my-config.yaml
```

### 3. Command Line Arguments

```bash
# Run with all parameters specified
python job_applier.py run \
    --email "your-email@example.com" \
    --password "your-password" \
    --cv "./data/cv.pdf" \
    --mcp-host "localhost" \
    --mcp-port 3000 \
    --format "rich" \
    --save
```

## Commands

### `run` - Execute Job Application Workflow

The main command that runs the complete job application workflow.

**Usage:**
```bash
python job_applier.py run [OPTIONS]
```

**Options:**
- `--config, -c FILE`: Configuration file path (YAML format)
- `--email, -e TEXT`: LinkedIn email address
- `--password, -p TEXT`: LinkedIn password
- `--cv FILE`: Path to CV file (PDF)
- `--mcp-host TEXT`: MCP server host (default: localhost)
- `--mcp-port INTEGER`: MCP server port (default: 3000)
- `--format, -f TEXT`: Output format - rich, simple, json (default: rich)
- `--save/--no-save`: Save results to file (default: save)
- `--interactive, -i`: Interactive mode for job search configuration

**Examples:**
```bash
# Interactive mode with rich output
python job_applier.py run --interactive

# Use configuration file
python job_applier.py run --config ./examples/config.yaml

# JSON output for scripting
python job_applier.py run --format json --config ./config.yaml

# Simple text output
python job_applier.py run --format simple --email user@example.com --password pass123 --cv ./cv.pdf
```

### `init` - Initialize Configuration

Creates a new configuration file with either default values or through interactive setup.

**Usage:**
```bash
python job_applier.py init [OPTIONS]
```

**Options:**
- `--config, -c FILE`: Configuration file path (default: ~/.job-applier/config.yaml)
- `--interactive/--no-interactive`: Interactive configuration (default: interactive)

**Examples:**
```bash
# Interactive configuration setup
python job_applier.py init

# Create default configuration
python job_applier.py init --no-interactive --config ./my-config.yaml

# Initialize in home directory
python job_applier.py init --config ~/.job-applier/config.yaml
```

### `validate` - Validate Configuration

Validates a configuration file for correctness and completeness.

**Usage:**
```bash
python job_applier.py validate [OPTIONS]
```

**Options:**
- `--config, -c FILE`: Configuration file path

**Examples:**
```bash
# Validate default configuration
python job_applier.py validate

# Validate specific configuration
python job_applier.py validate --config ./my-config.yaml
```

### `test-connection` - Test MCP Server Connection

Tests connectivity to the MCP server before running the workflow.

**Usage:**
```bash
python job_applier.py test-connection [OPTIONS]
```

**Options:**
- `--mcp-host TEXT`: MCP server host (default: localhost)
- `--mcp-port INTEGER`: MCP server port (default: 3000)

**Examples:**
```bash
# Test local connection
python job_applier.py test-connection

# Test remote connection
python job_applier.py test-connection --mcp-host 192.168.1.100 --mcp-port 3000
```

## Configuration File Format

The configuration file uses YAML format with the following structure:

```yaml
# LinkedIn credentials
linkedin_email: "your-email@example.com"
linkedin_password: "your-password"

# CV file path
cv_file_path: "./data/cv.pdf"

# MCP server configuration
mcp_server_host: "localhost"
mcp_server_port: 3000

# Job search criteria
job_searches:
  - job_title: "Python Developer"
    location: "Remote"
    monthly_salary: 5000
    limit: 20

  - job_title: "Software Engineer"
    location: "San Francisco"
    monthly_salary: 7000
    limit: 15

# Output configuration
output_format: "rich"  # Options: rich, simple, json
save_results: true
results_directory: "./results"

# Logging configuration
log_level: "INFO"  # Options: DEBUG, INFO, WARNING, ERROR
log_file: "./logs/job_applier.log"
```

### Job Search Configuration

Each job search entry supports:
- `job_title`: The job title to search for
- `location`: Geographic location or "Remote"
- `monthly_salary`: Expected monthly salary in USD
- `limit`: Maximum number of jobs to find (1-100)

## Output Formats

### Rich Format (Default)
- Beautiful terminal output with colors and formatting
- Progress indicators and interactive elements
- Tables, trees, and panels for organized display
- Real-time workflow progress

### Simple Format
- Plain text output suitable for logging
- Basic formatting without colors
- Good for terminal environments with limited formatting support

### JSON Format
- Machine-readable output for scripting and automation
- Complete workflow results in structured format
- Suitable for integration with other tools

## Environment Variables

The CLI respects the following environment variables (recommended approach for sensitive data):

### Required Variables:
- `LINKEDIN_EMAIL`: LinkedIn account email
- `LINKEDIN_PASSWORD`: LinkedIn account password
- `CV_FILE_PATH`: Path to CV file
- `HUGGING_FACE_HUB_TOKEN`: Hugging Face API token for AI inference

### MCP Server Configuration:
- `MCP_SERVER_HOST`: MCP server hostname (default: localhost)
- `MCP_SERVER_PORT`: MCP server port (default: 3000)
- `MCP_SERVER_COMMAND`: Command to start MCP server (default: python -m linkedin_mcp.linkedin.linkedin_server)

### Optional Configuration:
- `LOG_LEVEL`: Logging level (default: INFO)
- `LOG_FILE`: Log file path
- `OUTPUT_FORMAT`: Default output format (rich, simple, json)
- `RESULTS_DIRECTORY`: Directory for saving results (default: ./results)
- `SAVE_RESULTS`: Whether to save results (default: true)

**Important**: Environment variables take precedence over configuration file values. For security, credentials should always be set via environment variables rather than configuration files.

## Workflow Steps

The CLI executes the following workflow:

1. **Configuration Loading**: Load and validate configuration from multiple sources
2. **CV Analysis**: Read and analyze the CV file using AI
3. **Job Search**: Search LinkedIn for jobs matching criteria
4. **Job Filtering**: Filter jobs based on CV alignment using AI
5. **Job Application**: Apply to filtered jobs automatically
6. **Results Reporting**: Display and save workflow results

## Results and Logging

### Results Storage
- Results are automatically saved to `./results/` directory by default
- Each run creates a timestamped JSON file with complete results
- Configurable via `results_directory` setting

### Logging
- Console logging with configurable levels
- Optional file logging for persistent records
- Structured logging for troubleshooting

## Error Handling

The CLI provides comprehensive error handling:

- **Configuration Validation**: Checks for missing or invalid settings
- **Connection Testing**: Verifies MCP server connectivity
- **Workflow Errors**: Captures and reports errors during execution
- **Graceful Degradation**: Continues operation when possible despite errors

## Interactive Mode

Interactive mode allows dynamic configuration:

- **Job Search Setup**: Add multiple job searches interactively
- **Configuration Prompts**: Step-by-step configuration creation
- **Real-time Validation**: Immediate feedback on input validity

## Integration Examples

### Shell Scripts
```bash
#!/bin/bash
# Automated job application script
export LINKEDIN_EMAIL="user@example.com"
export LINKEDIN_PASSWORD="password123"

python job_applier.py run --config ./production-config.yaml --format json > results.json
if [ $? -eq 0 ]; then
    echo "Job application workflow completed successfully"
    # Process results.json as needed
else
    echo "Workflow failed"
    exit 1
fi
```

### Cron Jobs
```bash
# Run job applications daily at 9 AM
0 9 * * * cd /path/to/job-applier && python job_applier.py run --config ./config.yaml --format simple >> ./logs/daily-run.log 2>&1
```

### Docker Integration
```bash
# Run in Docker container
docker run --rm -v $(pwd)/data:/app/data -v $(pwd)/config.yaml:/app/config.yaml job-applier \
    python job_applier.py run --config /app/config.yaml
```

## Troubleshooting

### Common Issues

1. **Connection Refused**: MCP server not running
   ```bash
   python job_applier.py test-connection
   ```

2. **Authentication Failed**: Invalid LinkedIn credentials
   - Verify credentials with `validate` command
   - Check for special characters in password

3. **CV File Not Found**: Incorrect file path
   ```bash
   python job_applier.py validate --config ./config.yaml
   ```

4. **No Jobs Found**: Search criteria too restrictive
   - Review job search configuration
   - Try broader location or title terms

### Debug Mode
```bash
# Run with debug logging
python job_applier.py run --config ./config.yaml 2>&1 | tee debug.log
```

### Verbose Output
For troubleshooting, use simple format for detailed logging:
```bash
python job_applier.py run --format simple --config ./config.yaml
```
