#!/usr/bin/env python3

import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions
from mcp.types import Resource, TextContent, Tool
from pydantic import AnyUrl


class StravaAPI:
    def __init__(self, client_id: str, client_secret: str, refresh_token: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    async def refresh_access_token(self):
        """Refresh the access token using the refresh token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://www.strava.com/oauth/token",
                data={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "refresh_token": self.refresh_token,
                    "grant_type": "refresh_token"
                }
            )
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data["refresh_token"]
            expires_in = token_data["expires_in"]
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)

    async def ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if not self.access_token or (
            self.token_expires_at and datetime.now() >= self.token_expires_at - timedelta(minutes=5)
        ):
            await self.refresh_access_token()

    async def get_activities(self, before: Optional[int] = None, after: Optional[int] = None, per_page: int = 30) -> List[Dict[str, Any]]:
        """Get athlete activities"""
        await self.ensure_valid_token()
        
        params = {"per_page": per_page}
        if before:
            params["before"] = before
        if after:
            params["after"] = after

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.strava.com/api/v3/athlete/activities",
                headers={"Authorization": f"Bearer {self.access_token}"},
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def get_athlete(self) -> Dict[str, Any]:
        """Get athlete information"""
        await self.ensure_valid_token()
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.strava.com/api/v3/athlete",
                headers={"Authorization": f"Bearer {self.access_token}"}
            )
            response.raise_for_status()
            return response.json()


def meters_to_miles(meters: float) -> float:
    """Convert meters to miles"""
    return meters * 0.000621371


def meters_per_second_to_pace(mps: float) -> str:
    """Convert meters per second to pace (min:sec per mile)"""
    if mps == 0:
        return "N/A"
    
    miles_per_second = mps * 0.000621371
    seconds_per_mile = 1 / miles_per_second
    minutes = int(seconds_per_mile // 60)
    seconds = int(seconds_per_mile % 60)
    return f"{minutes}:{seconds:02d}"


app = Server("strava-marathon-coach")
strava_api: Optional[StravaAPI] = None


@app.list_tools()
async def handle_list_tools() -> List[Tool]:
    """List available tools"""
    return [
        Tool(
            name="get_recent_runs",
            description="Get recent running activities from Strava",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Number of days back to fetch activities (default: 30)",
                        "default": 30
                    }
                }
            }
        ),
        Tool(
            name="get_weekly_mileage",
            description="Calculate weekly mileage totals for recent weeks",
            inputSchema={
                "type": "object", 
                "properties": {
                    "weeks": {
                        "type": "integer",
                        "description": "Number of weeks to analyze (default: 4)",
                        "default": 4
                    }
                }
            }
        ),
        Tool(
            name="analyze_pace_trends",
            description="Analyze pace trends over recent runs",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer", 
                        "description": "Number of days back to analyze (default: 30)",
                        "default": 30
                    }
                }
            }
        )
    ]


@app.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls"""
    if not strava_api:
        return [TextContent(type="text", text="Strava API not initialized")]

    try:
        if name == "get_recent_runs":
            days = arguments.get("days", 30)
            after_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
            
            activities = await strava_api.get_activities(after=after_timestamp)
            
            # Filter for running activities
            runs = [activity for activity in activities if activity["type"] == "Run"]
            
            if not runs:
                return [TextContent(type="text", text="No running activities found in the specified period.")]
            
            result = f"Found {len(runs)} running activities in the last {days} days:\n\n"
            
            for run in runs:
                date = datetime.fromisoformat(run["start_date_local"].replace("Z", "+00:00"))
                distance_miles = meters_to_miles(run["distance"])
                avg_pace = meters_per_second_to_pace(run["average_speed"]) if run["average_speed"] else "N/A"
                
                result += f"• {date.strftime('%Y-%m-%d')}: {run['name']}\n"
                result += f"  Distance: {distance_miles:.2f} miles\n"
                result += f"  Avg Pace: {avg_pace}/mile\n"
                result += f"  Duration: {run['elapsed_time'] // 60}:{run['elapsed_time'] % 60:02d}\n\n"
            
            return [TextContent(type="text", text=result)]

        elif name == "get_weekly_mileage":
            weeks = arguments.get("weeks", 4)
            days_back = weeks * 7
            after_timestamp = int((datetime.now() - timedelta(days=days_back)).timestamp())
            
            activities = await strava_api.get_activities(after=after_timestamp)
            runs = [activity for activity in activities if activity["type"] == "Run"]
            
            # Group runs by week
            weekly_mileage = {}
            for run in runs:
                date = datetime.fromisoformat(run["start_date_local"].replace("Z", "+00:00"))
                week_start = date - timedelta(days=date.weekday())
                week_key = week_start.strftime("%Y-%m-%d")
                
                if week_key not in weekly_mileage:
                    weekly_mileage[week_key] = 0
                
                weekly_mileage[week_key] += meters_to_miles(run["distance"])
            
            if not weekly_mileage:
                return [TextContent(type="text", text="No running activities found for weekly mileage calculation.")]
            
            result = f"Weekly mileage for the last {weeks} weeks:\n\n"
            
            for week_start in sorted(weekly_mileage.keys(), reverse=True):
                result += f"Week of {week_start}: {weekly_mileage[week_start]:.1f} miles\n"
            
            total_mileage = sum(weekly_mileage.values())
            avg_weekly = total_mileage / len(weekly_mileage)
            result += f"\nTotal: {total_mileage:.1f} miles\n"
            result += f"Average per week: {avg_weekly:.1f} miles"
            
            return [TextContent(type="text", text=result)]

        elif name == "analyze_pace_trends":
            days = arguments.get("days", 30)
            after_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
            
            activities = await strava_api.get_activities(after=after_timestamp)
            runs = [activity for activity in activities if activity["type"] == "Run" and activity["average_speed"]]
            
            if not runs:
                return [TextContent(type="text", text="No running activities with pace data found.")]
            
            # Sort by date
            runs.sort(key=lambda x: x["start_date_local"])
            
            result = f"Pace analysis for the last {days} days:\n\n"
            
            paces = []
            for run in runs:
                pace_seconds = 1 / (run["average_speed"] * 0.000621371)  # seconds per mile
                paces.append(pace_seconds)
                
                date = datetime.fromisoformat(run["start_date_local"].replace("Z", "+00:00"))
                pace_str = meters_per_second_to_pace(run["average_speed"])
                distance_miles = meters_to_miles(run["distance"])
                
                result += f"{date.strftime('%m/%d')}: {pace_str}/mile ({distance_miles:.1f}mi)\n"
            
            if len(paces) >= 2:
                avg_pace = sum(paces) / len(paces)
                avg_pace_str = f"{int(avg_pace // 60)}:{int(avg_pace % 60):02d}"
                
                recent_avg = sum(paces[-3:]) / min(3, len(paces))
                early_avg = sum(paces[:3]) / min(3, len(paces))
                
                trend = "improving" if recent_avg < early_avg else "declining"
                if abs(recent_avg - early_avg) < 10:  # within 10 seconds
                    trend = "stable"
                
                result += f"\nAverage pace: {avg_pace_str}/mile\n"
                result += f"Trend: {trend}"
            
            return [TextContent(type="text", text=result)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main function to run the MCP server"""
    global strava_api
    
    # Initialize Strava API
    client_id = os.getenv("STRAVA_CLIENT_ID")
    client_secret = os.getenv("STRAVA_CLIENT_SECRET")
    refresh_token = os.getenv("STRAVA_REFRESH_TOKEN")
    
    if not all([client_id, client_secret, refresh_token]):
        raise ValueError("Missing required environment variables: STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_REFRESH_TOKEN")
    
    strava_api = StravaAPI(client_id, client_secret, refresh_token)
    
    # Run the server
    from mcp.server.stdio import stdio_server
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="strava-marathon-coach",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={}
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())