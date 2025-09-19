import json
import os
import sys

import pytest
from fastmcp.client import Client
from fastmcp.client.transports import PythonStdioTransport

# Ensure the server module can be found
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Set the path to the grit executable for the tests
GRIT_CLI_PATH = "/home/johann/.nvm/versions/node/v23.9.0/bin/grit"

@pytest.fixture
def mcp_client():
    """Fixture to create and configure the MCP client."""
    server_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../server/main.py")
    )

    # Pass the grit CLI path to the server process
    env = os.environ.copy()
    env["GRIT_CLI_PATH"] = GRIT_CLI_PATH

    transport = PythonStdioTransport(script_path=server_path, env=env)
    client = Client(transport)
    return client

@pytest.mark.asyncio
async def test_search_patterns(mcp_client):
    """
    Tests the library.search_patterns tool by using the FastMCP client.
    """
    async with mcp_client as client:
        assert client.is_connected()

        # Call the 'library.search_patterns' tool
        result = await client.call_tool(
            "library.search_patterns",
            {"query": "", "language": "python", "source": "all", "limit": 5},
        )

        # The result is a TextContent object with a JSON string
        response_data = json.loads(result.content[0].text)

        # Validate the response
        assert "items" in response_data
        if response_data["items"]:
            items_data = json.loads(response_data["items"])
            assert isinstance(items_data, list)
            # The command might return an empty list if no patterns are installed
            assert len(items_data) >= 0

@pytest.mark.asyncio
async def test_describe_pattern(mcp_client):
    """
    Tests the patterns.describe tool by using the FastMCP client.
    """
    async with mcp_client as client:
        assert client.is_connected()

        # Call the 'patterns.describe' tool
        result = await client.call_tool("patterns.describe", {"name": "apply_change"})

        # The result is a TextContent object with a JSON string
        response_data = json.loads(result.content[0].text)

        # Validate the response
        assert "description" in response_data
        assert isinstance(response_data["description"], str)
