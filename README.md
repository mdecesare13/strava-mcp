# Strava MCP Server

A Model Context Protocol (MCP) server that integrates Strava data for marathon coaching and training analysis. This server enables Claude Desktop to access your Strava activities and provide personalized running insights.

## Features

- **Recent Activity Analysis** - Fetch and analyze your recent running activities
- **Weekly Mileage Tracking** - Calculate weekly mileage totals and trends
- **Pace Trend Analysis** - Analyze pace improvements and patterns over time
- **Automatic Token Management** - Handles Strava API token refresh automatically

## Quick Setup

### 1. Prerequisites

- Python 3.8 or higher
- Strava account with API access
- Claude Desktop application

### 2. Clone and Install

```bash
git clone <repository-url>
cd strava-mcp
pip install -r requirements.txt
```

### 3. Configure Strava API

1. Create a Strava API application at [developers.strava.com](https://developers.strava.com)
2. Copy `.env-template` to `.env`:
   ```bash
   cp .env-template .env
   ```
3. Fill in your actual Strava API credentials in `.env`:
   ```
   STRAVA_CLIENT_ID=your_actual_client_id
   STRAVA_CLIENT_SECRET=your_actual_client_secret
   STRAVA_REFRESH_TOKEN=your_actual_refresh_token
   ```

### 4. Test the Server

```bash
python strava_mcp_server.py
```

The server should start without errors. Press Ctrl+C to stop it.

### 5. Configure Claude Desktop

Add this configuration to your Claude Desktop MCP settings:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "strava-marathon-coach": {
      "command": "python",
      "args": ["/absolute/path/to/strava_mcp_server.py"],
      "env": {
        "STRAVA_CLIENT_ID": "your_client_id",
        "STRAVA_CLIENT_SECRET": "your_client_secret",
        "STRAVA_REFRESH_TOKEN": "your_refresh_token"
      }
    }
  }
}
```

**Important:** Use the absolute path to your `strava_mcp_server.py` file.

### 6. Restart Claude Desktop

Restart Claude Desktop completely for the MCP server to be recognized.

## Available Tools

| Tool | Description | Default Parameters |
|------|-------------|-------------------|
| `get_recent_runs` | Fetches recent running activities | Last 30 days |
| `get_weekly_mileage` | Calculates weekly mileage totals | Last 4 weeks |
| `analyze_pace_trends` | Analyzes pace trends over time | Last 30 days |

## Usage Examples

Once configured, ask Claude:

- "What are my recent runs?"
- "Show me my weekly mileage for the past 4 weeks"
- "Analyze my pace trends"
- "How is my marathon training progressing?"

## Security Notes

- Never commit your `.env` file to version control
- Keep your Strava API credentials secure
- The `.env-template` file shows the required format but contains example values only

## Troubleshooting

### Server Won't Start
- Verify all environment variables are set in `.env`
- Check Python package installation: `pip install -r requirements.txt`
- Validate Strava API credentials

### Claude Can't Connect
- Ensure absolute path in Claude Desktop config
- Verify environment variables in config match your actual credentials
- Restart Claude Desktop after config changes
- Check Claude Desktop logs for connection errors

### API Errors
- Refresh token may be expired - re-authorize your Strava app
- Verify your Strava API app has "read activities" permissions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details