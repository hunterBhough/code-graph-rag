# LaunchAgent for graph-code

Auto-generated LaunchAgent configuration for running graph-code HTTP server as a macOS background service.

**Generated**: 2025-12-11T16:22:29.154434+00:00

## Overview

This LaunchAgent enables graph-code to:
- Start automatically on system boot
- Restart automatically if the process crashes
- Run as a background service
- Manage logs automatically

## Files

- `service.plist` - LaunchAgent configuration
- `install.sh` - Installation script
- `README.md` - This file

## Quick Start

### Install and Start

```bash
./install.sh
```

This will:
1. Verify prerequisites
2. Unload any existing instance
3. Install the plist to `~/Library/LaunchAgents/`
4. Load and start the service
5. Verify the service is running

### Verify Running

```bash
# Check service status
launchctl list | grep graph-code

# Test health endpoint
curl http://127.0.0.1:9001/health

# View available tools
curl http://127.0.0.1:9001/tools
```

## Management Commands

### Status

```bash
launchctl list | grep com.ai-agency.graph-code
```

Shows service status and PID if running.

### Stop

```bash
launchctl unload ~/Library/LaunchAgents/com.ai-agency.graph-code.plist
```

Stops the service but leaves it installed.

### Start

```bash
launchctl load ~/Library/LaunchAgents/com.ai-agency.graph-code.plist
```

Starts the service if it's currently stopped.

### Restart

```bash
launchctl unload ~/Library/LaunchAgents/com.ai-agency.graph-code.plist && \
launchctl load ~/Library/LaunchAgents/com.ai-agency.graph-code.plist
```

Restarts the service.

### Uninstall

```bash
launchctl unload ~/Library/LaunchAgents/com.ai-agency.graph-code.plist
rm ~/Library/LaunchAgents/com.ai-agency.graph-code.plist
```

Stops and removes the service completely.

## Configuration

### Service Details

- **Label**: `com.ai-agency.graph-code`
- **Endpoint**: `http://127.0.0.1:9001`
- **Working Directory**: `/Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag`
- **Python**: `/Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag/.venv/bin/python`
- **Server**: `/Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag/http_server/server.py`

### Logs

Logs are written to `/Users/hunter/Library/Logs`:

- **stdout**: `graph-code-stdout.log` - Normal output and info messages
- **stderr**: `graph-code-stderr.log` - Error messages and stack traces

#### View Logs

```bash
# View all logs
tail -f /Users/hunter/Library/Logs/graph-code-*.log

# View stdout only
tail -f /Users/hunter/Library/Logs/graph-code-stdout.log

# View stderr only
tail -f /Users/hunter/Library/Logs/graph-code-stderr.log

# View recent errors
grep -i error /Users/hunter/Library/Logs/graph-code-stderr.log
```

### Environment Variables

The LaunchAgent sets these environment variables:

- `PORT=9001` - HTTP server port
- `HOST=127.0.0.1` - HTTP server host
- `PYTHONUNBUFFERED=1` - Disable Python output buffering

### Auto-Restart Behavior

The service will automatically restart if:
- The process exits with a non-zero status code
- The process crashes
- The process terminates unexpectedly

**Throttle Interval**: 10 seconds between restart attempts to prevent rapid restart loops.

## Troubleshooting

### Service Won't Start

1. Check prerequisites:
   ```bash
   /Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag/.venv/bin/python --version
   ```

2. Check plist syntax:
   ```bash
   plutil -lint ~/Library/LaunchAgents/com.ai-agency.graph-code.plist
   ```

3. Check logs for errors:
   ```bash
   tail -50 /Users/hunter/Library/Logs/graph-code-stderr.log
   ```

### Service Keeps Restarting

1. Check stderr logs for crash reasons:
   ```bash
   tail -100 /Users/hunter/Library/Logs/graph-code-stderr.log
   ```

2. Look for Python/Node errors or missing dependencies

3. Try running the server manually to see the error:
   ```bash
   cd /Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag
   /Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag/.venv/bin/python /Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag/http_server/server.py
   ```

### Port Already in Use

If port 9001 is already in use:

1. Find what's using the port:
   ```bash
   lsof -i :9001
   ```

2. Either stop that service or regenerate with a different port:
   ```bash
   python -m generator --bootstrap-http --mcp-path /Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag --port <NEW_PORT>
   ```

### Health Endpoint Not Responding

1. Verify service is running:
   ```bash
   launchctl list | grep graph-code
   ```

2. Check if port is listening:
   ```bash
   lsof -i :9001
   ```

3. Try with verbose curl:
   ```bash
   curl -v http://127.0.0.1:9001/health
   ```

4. Check firewall settings:
   ```bash
   sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
   ```

### Unload Fails with "Could not find specified service"

This means the service isn't currently loaded. You can safely install without unloading first.

## HTTP API

### Health Check

```bash
curl http://127.0.0.1:9001/health
```

**Response**: `{"status": "ok", "service": "graph-code", ...}`

### List Tools

```bash
curl http://127.0.0.1:9001/tools
```

**Response**: Service info and available tool schemas

### Call Tool

```bash
curl -X POST http://127.0.0.1:9001/call-tool \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "example_tool",
    "arguments": {}
  }'
```

**Response**: Tool execution result

## Best Practices

1. **Always check logs after installation** to ensure the service started cleanly
2. **Monitor the stderr log** for any recurring errors
3. **Test the health endpoint** before relying on the service
4. **Keep backups** of customized plist files before regenerating
5. **Use descriptive tool names** to make debugging easier
6. **Set up monitoring** for production services (e.g., check health endpoint periodically)

## System Requirements

- macOS 10.10 (Yosemite) or later
- Python 3.12+
- Network access on 127.0.0.1:9001

## Security Notes

- The service runs under your user account (not as root)
- Logs may contain sensitive information - review log contents
- The HTTP server binds to 127.0.0.1 by default (localhost only)
- To expose externally, modify the plist to bind to 0.0.0.0 (not recommended without authentication)

## Support

For issues with the LaunchAgent:
1. Check the troubleshooting section above
2. Review logs in `/Users/hunter/Library/Logs`
3. Test the server manually outside of LaunchAgent
4. Regenerate the LaunchAgent configuration if needed

## Regeneration

To regenerate this LaunchAgent configuration:

```bash
cd /path/to/http-service-wrappers
python -m generator --bootstrap-http --mcp-path /Users/hunter/code/ai_agency/shared/mcp-servers/code-graph-rag
```

This will overwrite the existing LaunchAgent files but preserve any custom modifications to the HTTP server itself.