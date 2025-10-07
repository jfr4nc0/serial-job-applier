# LinkedIn Job Application Agent - Logging & Debugging Guide

## Overview

The LinkedIn Job Application Agent implements comprehensive logging with trace ID correlation across both the **Core Agent** and **LinkedIn MCP Server** components for effective debugging and monitoring.

## 🏗️ Logging Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Core Agent    │    │  LinkedIn MCP   │    │   Langfuse      │
│                 │    │     Server      │    │ (Observability) │
│ ┌─────────────┐ │    │ ┌─────────────┐ │    │ ┌─────────────┐ │
│ │   Loguru    │ │    │ │   Loguru    │ │    │ │   Traces    │ │
│ │  Structured │ │────│ │  Structured │ │────│ │  & Spans    │ │
│ │   Logging   │ │    │ │   Logging   │ │    │ │             │ │
│ └─────────────┘ │    │ └─────────────┘ │    │ └─────────────┘ │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Unified Trace ID                            │
│         f604a509-0c54-4529-8643-39eb7525a39b                   │
└─────────────────────────────────────────────────────────────────┘
```

## 📁 Log File Structure

After setup, you'll have:

```
logs/
├── core_agent.log         # Core agent workflow logs
├── linkedin_mcp.log       # LinkedIn MCP server logs
├── job_applier.log        # General application logs
└── archive/               # Rotated/compressed logs
```

## 🚀 Quick Setup

### 1. Run the Setup Script
```bash
./scripts/setup_logging.sh
```

### 2. Configure Environment Variables
Add to your `.env` file:

```bash
# Core Agent Logging
CORE_AGENT_LOG_LEVEL=INFO
CORE_AGENT_LOG_FILE=./logs/core_agent.log

# LinkedIn MCP Server Logging
LINKEDIN_MCP_LOG_LEVEL=INFO
LINKEDIN_MCP_LOG_FILE=./logs/linkedin_mcp.log

# General Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/job_applier.log
```

### 3. Start the Application
```bash
python -m cli.client run
```

## 📊 Log Levels

| Level    | When to Use | Examples |
|----------|-------------|----------|
| `DEBUG`  | Development troubleshooting | Internal state changes, detailed flow |
| `INFO`   | Normal operations | Workflow steps, successful operations |
| `WARNING`| Recoverable issues | Missing optional configs, retries |
| `ERROR`  | Operation failures | Authentication failures, job apply errors |
| `CRITICAL`| System failures | Database connections, critical services |

## 🔍 Log Format

### Core Agent Logs
```
2025-10-07 12:37:31.921 | INFO     | core-agent | src.core.agent:read_cv_node:63 | trace_id=abc123... | Starting CV analysis cv_file_path=/app/data/cv.pdf
```

### LinkedIn MCP Logs
```
2025-10-07 12:37:32.150 | INFO     | linkedin-mcp | mcp-12345 | linkedin_mcp.linkedin.services:apply_to_jobs:67 | trace_id=abc123... | Starting LinkedIn job application workflow applications_count=5
```

### Fields Explained
- **Timestamp**: `2025-10-07 12:37:31.921`
- **Level**: `INFO`, `ERROR`, etc.
- **Component**: `core-agent` or `linkedin-mcp`
- **Server ID**: `mcp-12345` (for MCP server)
- **Location**: `module:function:line`
- **Trace ID**: `trace_id=abc123...` (UUID for correlation)
- **Message**: Human-readable description
- **Context**: Structured data (file paths, counts, etc.)

## 🔗 Trace ID Correlation

Every workflow execution gets a unique UUID trace ID that flows through:

1. **Core Agent** generates trace ID
2. **LinkedIn MCP Client** receives trace ID
3. **LinkedIn MCP Server** inherits trace ID
4. **All operations** logged with same trace ID
5. **Langfuse observability** (if configured) correlates everything

### Example: Finding All Logs for One Job Application
```bash
# Get trace ID from first log entry
grep "Starting LinkedIn job application workflow" logs/core_agent.log

# Find all related logs
grep "trace_id=f604a509" logs/*.log
```

## 🛠️ Debugging Common Issues

### Issue: No logs appearing
```bash
# Check if logging is configured
echo $CORE_AGENT_LOG_FILE
echo $LINKEDIN_MCP_LOG_FILE

# Check permissions
ls -la logs/

# Check log level
grep "LOG_LEVEL" .env
```

### Issue: MCP server not logging
```bash
# Run MCP server directly to see console output
python -m linkedin_mcp.linkedin.linkedin_server

# Check if MCP log file exists
ls -la logs/linkedin_mcp.log
```

### Issue: Trace IDs not matching
```bash
# Verify trace ID propagation
grep -A 5 -B 5 "trace_id" logs/core_agent.log | head -20
```

## 📈 Log Monitoring

### Real-time Monitoring
```bash
# Watch all logs
tail -f logs/*.log

# Watch specific component
tail -f logs/core_agent.log

# Watch errors only
tail -f logs/*.log | grep ERROR
```

### Log Analysis
```bash
# Count errors by type
grep "ERROR" logs/*.log | cut -d'|' -f6 | sort | uniq -c

# Find longest running operations
grep "duration_ms" logs/linkedin_mcp.log | sort -k8 -n

# Track success rates
grep "success=" logs/linkedin_mcp.log | grep -o "success=[^|]*" | sort | uniq -c
```

### Structured Log Parsing
```bash
# Extract all trace IDs from today
grep "$(date +%Y-%m-%d)" logs/*.log | grep -o "trace_id=[^|]*" | sort | uniq

# Find workflow completion times
grep "workflow completed" logs/*.log | grep -o "[0-9][0-9]:[0-9][0-9]:[0-9][0-9]"
```

## 🔧 Advanced Configuration

### Custom Log Rotation
```python
# In logging_config.py, modify rotation settings:
logger.add(
    log_file,
    rotation="50 MB",        # Rotate at 50MB
    retention="30 days",     # Keep for 30 days
    compression="gzip",      # Compress old logs
)
```

### Development Debug Mode
```bash
# Enable maximum verbosity
export CORE_AGENT_LOG_LEVEL=DEBUG
export LINKEDIN_MCP_LOG_LEVEL=DEBUG
python -m cli.client run
```

### Production Monitoring
```bash
# Add to your monitoring stack
tail -f logs/linkedin_mcp.log | grep "ERROR\|CRITICAL" | your-monitoring-tool
```

## 📋 Log Retention Policy

- **Active logs**: Unlimited size (rotated at 10MB)
- **Archived logs**: 7 days retention
- **Compression**: gzip for archived logs
- **Location**: `logs/archive/` directory

## 🚨 Error Investigation Workflow

1. **Identify the issue**:
   ```bash
   grep "ERROR\|CRITICAL" logs/*.log | tail -10
   ```

2. **Get the trace ID**:
   ```bash
   grep "trace_id=" logs/core_agent.log | tail -1
   ```

3. **Follow the complete workflow**:
   ```bash
   grep "trace_id=YOUR_TRACE_ID" logs/*.log | sort
   ```

4. **Check for patterns**:
   ```bash
   grep "trace_id=YOUR_TRACE_ID" logs/*.log | grep -E "(ERROR|exception|failed)"
   ```

5. **Verify MCP communication**:
   ```bash
   grep "trace_id=YOUR_TRACE_ID" logs/linkedin_mcp.log
   ```

## 💡 Tips & Best Practices

### Development
- Use `DEBUG` level for development
- Watch logs in real-time: `tail -f logs/*.log`
- Use trace IDs to follow execution flow

### Production
- Use `INFO` level for production
- Set up log monitoring/alerting
- Regularly archive old logs

### Troubleshooting
- Always start with trace ID correlation
- Check both core agent and MCP logs
- Look for error patterns across components
- Use structured data for filtering

## 🔗 Integration with Observability

When Langfuse is configured, logs are enhanced with:
- **Distributed tracing** across components
- **Performance metrics** for LangGraph nodes
- **Error correlation** with full context
- **User journey tracking** end-to-end

See observability documentation for Langfuse setup details.

## 📞 Support

If you encounter logging issues:

1. **Check log file permissions**: `ls -la logs/`
2. **Verify environment variables**: `env | grep LOG`
3. **Test basic logging**: `python -c "from loguru import logger; logger.info('test')"`
4. **Check disk space**: `df -h`

Happy debugging! 🐛🔍
