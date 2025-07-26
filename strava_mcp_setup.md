# Strava MCP Server Setup Guide

## Quick Setup (5-10 minutes)

### 1. Install Dependencies

First, create a new directory and install the required packages:

```bash
mkdir strava-mcp-server
cd strava-mcp-server

# Create requirements.txt
cat > requirements.txt << EOF
mcp>=1.0.0
httpx>=0.27.0
pydantic>=2.0.0
EOF

# Install dependencies
pip install -r requirements.txt
```

### 2. Save the Server Code

Save the Python server code as `strava_mcp_server.py` in your directory.

### 3. Set Environment Variables

Create a `.env` file or set these environment variables:

```bash
export STRAVA_CLIENT_ID="your_client_id_here"
export STRAVA_CLIENT_SECRET="your_client_secret_here" 
export STRAVA_REFRESH_TOKEN="your_refresh_token_here"
```

Or create a `.env` file:
```
STRAVA_CLIENT_ID=your_client_id_here
STRAVA_CLIENT_SECRET=your_client_secret_here
STRAVA_REFRESH_TOKEN=your_refresh_token_here
```

### 4. Test the Server

Test that the server runs correctly:

```bash
python strava_mcp_server.py
```

The server should start without errors. Press Ctrl+C to stop it.

### 5. Configure Claude Desktop

Add this configuration to your Claude Desktop MCP settings:

**For Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**For Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "strava-marathon-coach": {
      "command": "python",
      "args": ["/full/path/to/your/strava_mcp_server.py"],
      "env": {
        "STRAVA_CLIENT_ID": "your_client_id_here",
        "STRAVA_CLIENT_SECRET": "your_client_secret_here",
        "STRAVA_REFRESH_TOKEN": "your_refresh_token_here"
      }
    }
  }
}
```

**Important:** Replace `/full/path/to/your/strava_mcp_server.py` with the actual full path to your server file.

### 6. Restart Claude Desktop

Restart Claude Desktop completely for the MCP server to be recognized.

### 7. Test in Claude

In your marathon coaching project, try asking:
- "What are my recent runs?"
- "Show me my weekly mileage for the past 4 weeks"
- "Analyze my pace trends"

## Available Tools

Your MCP server provides three tools:

1. **get_recent_runs** - Fetches recent running activities (default: 30 days)
2. **get_weekly_mileage** - Calculates weekly mileage totals (default: 4 weeks)
3. **analyze_pace_trends** - Analyzes pace trends over recent runs (default: 30 days)

## Troubleshooting

### Server Won't Start
- Check that all environment variables are set correctly
- Verify you have the required Python packages installed
- Make sure your Strava API credentials are valid

### Claude Can't Connect
- Verify the path in your config file is absolute and correct
- Check that the environment variables are set in the config
- Restart Claude Desktop after making config changes
- Check Claude Desktop logs for connection errors

### API Errors
- Your refresh token might be expired - you may need to re-authorize your Strava app
- Check that your Strava API app has the correct permissions (read activities)

## Next Steps

Once connected, Claude will be able to:
- Analyze your recent training patterns
- Calculate weekly mileage trends
- Provide pace analysis and coaching insights
- Help adjust your marathon training plan based on actual performance data

The server automatically handles token refresh, so it should work continuously once set up!