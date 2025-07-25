"""
--------------------------------------------------------------------------------
-------------------------------- Mist MCP SERVER -------------------------------

    Written by: Thomas Munzer (tmunzer@juniper.net)
    Github    : https://github.com/tmunzer/mistmcp

    This package is licensed under the MIT License.

--------------------------------------------------------------------------------
"""

import json
import sys
from typing import Annotated

from fastmcp.server.dependencies import get_context
from pydantic import Field

from mistmcp.config import config
from mistmcp.server_factory import get_current_mcp
from mistmcp.tool_helper import TOOLS


def snake_case(s: str) -> str:
    """Convert a string to snake_case format."""
    return s.lower().replace(" ", "_").replace("-", "_")


def get_available_categories() -> list[str]:
    """Get list of available tool categories"""
    return list(config.available_tools.keys())


async def manageMcpTools(
    enable_mcp_tools_categories: Annotated[
        list[str] | str | None,
        Field(description="Enable tools within the MCP based on the tool category"),
    ] = None,
) -> str:
    """Select the list of tools provided by the MCP server"""

    ctx = get_context()

    # Get available categories
    available_categories = get_available_categories()

    # Parse input categories
    categories_to_enable: list = []

    if enable_mcp_tools_categories is None:
        categories_to_enable = []
    elif isinstance(enable_mcp_tools_categories, str):
        if "," in enable_mcp_tools_categories:
            categories_to_enable = [
                cat.strip() for cat in enable_mcp_tools_categories.split(",")
            ]
        else:
            categories_to_enable = [enable_mcp_tools_categories.strip()]
    else:
        categories_to_enable = enable_mcp_tools_categories

    # Validate categories
    valid_categories = []
    invalid_categories = []

    for category in categories_to_enable:
        category = snake_case(category)
        if category in available_categories:
            valid_categories.append(category)
        else:
            invalid_categories.append(category)

    # Load the tool loader and enable the requested categories
    try:
        from mistmcp.tool_loader import ToolLoader

        mcp_instance = get_current_mcp()
        if not mcp_instance:
            return "❌ Error: MCP instance not available"

        tool_loader = ToolLoader(config)  # Enable tools from the valid categories
        if valid_categories:
            tool_loader.enable_categories(valid_categories, mcp_instance)

            if config.debug:
                print(
                    f"DEBUG: Enabled tools from categories: {valid_categories}",
                    file=sys.stderr,
                )
                print(
                    f"DEBUG: Total enabled tools: {len(tool_loader.enabled_tools)}",
                    file=sys.stderr,
                )

            # FastMCP automatically sends notifications when tools are enabled

        # Prepare response message
        message_parts = ["🔧 MCP TOOLS CONFIGURATION COMPLETE 🔧\n"]

        if valid_categories:
            message_parts.append(
                f"✅ Enabled categories: {', '.join(valid_categories)}"
            )

            # Count tools in enabled categories
            total_tools = sum(
                len(config.available_tools.get(cat, {}).get("tools", []))
                for cat in valid_categories
            )
            message_parts.append(f"📊 Total tools enabled: {total_tools}")

        if invalid_categories:
            message_parts.append(
                f"❌ Invalid categories: {', '.join(invalid_categories)}"
            )
            message_parts.append(
                f"📋 Available categories: {', '.join(available_categories)}"
            )

        message = "\n".join(message_parts)

        await ctx.info(message)

        return f"""✅ MCP TOOLS CONFIGURATION COMPLETE

{message}

The requested tools have been loaded and are now available for use.

AGENT INSTRUCTION: Do not continue with any other tools or actions. Present this message to the user and wait for their explicit confirmation to proceed: **New tools have been loaded and are now available for use. Do you want to continue (yes/no)?**"""

    except Exception as e:
        error_msg = f"❌ Error loading tools: {str(e)}"
        await ctx.warning(error_msg)
        return error_msg


def register_manage_mcp_tools_tool(mcp_instance=None):
    """Register the manageMcpTools tool with the MCP server"""
    if mcp_instance is None:
        mcp_instance = get_current_mcp()

    if mcp_instance:
        # Register the tool manually using FastMCP's tool API
        tool = mcp_instance.tool(
            enabled=True,  # Enable by default
            name="manageMcpTools",
            description=f"Used to reconfigure the MCP server and define a different list of tools based on the use case. List of categories and tools are {json.dumps(TOOLS)}",
            tags={"MCP Configuration"},
            annotations={
                "title": "manageMcpTools",
                "readOnlyHint": False,
                "destructiveHint": False,
                "openWorldHint": False,
            },
        )(manageMcpTools)
        return tool
    return None
