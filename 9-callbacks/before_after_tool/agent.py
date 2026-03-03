"""
Before and After Tool Callbacks Example

This example demonstrates using tool callbacks to modify tool behavior.
"""

import copy
from typing import Any, Dict, Optional

from google.adk.agents import LlmAgent
from google.adk.tools.base_tool import BaseTool
from google.adk.tools.tool_context import ToolContext


# --- Define a Simple Tool Function ---
def get_capital_city(country: str) -> Dict[str, str]:
    """
    Retrieves the capital city of a given country.

    Args:
        country: Name of the country

    Returns:
        Dictionary with the capital city result
    """
    print(f"[TOOL] Executing get_capital_city tool with country: {country}")

    country_capitals = {
        "united states": "Washington, D.C.",
        "usa": "Washington, D.C.",
        "canada": "Ottawa",
        "france": "Paris",
        "germany": "Berlin",
        "japan": "Tokyo",
        "brazil": "Brasília",
        "australia": "Canberra",
        "india": "New Delhi",
    }

    # Use lowercase for comparison
    result = country_capitals.get(country.lower(), f"Capital not found for {country}")
    print(f"[TOOL] Result: {result}")
    
    return {"result": result}


# --- Define Before Tool Callback ---
def before_tool_callback(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext
) -> Optional[Dict]:
    """
    Simple callback that modifies tool arguments or skips the tool call.
    """
    tool_name = tool.name
    print(f"[Callback] Before tool call for '{tool_name}'")

    # If someone asks about 'Merica, convert to United States
    if tool_name == "get_capital_city" and args.get("country", "").lower() == "merica":
        print("[Callback] Converting 'Merica to 'United States'")
        args["country"] = "United States"
        return None

    # Skip the call completely for restricted countries
    if (
        tool_name == "get_capital_city"
        and args.get("country", "").lower() == "restricted"
    ):
        print("[Callback] Blocking restricted country")
        return {"result": "Access to this information has been restricted."}

    return None


# --- Define After Tool Callback ---
def after_tool_callback(
    tool: BaseTool, args: Dict[str, Any], tool_context: ToolContext, tool_response: Dict
) -> Optional[Dict]:
    """
    Simple callback that modifies the tool response after execution.
    """
    tool_name = tool.name
    print(f"[Callback] After tool call for '{tool_name}'")

    original_result = tool_response.get("result", "")

    # Add a note for any USA capital responses
    if tool_name == "get_capital_city" and "washington" in original_result.lower():
        print("[Callback] DETECTED USA CAPITAL - adding patriotic note!")

        # Create a modified copy of the response
        modified_response = copy.deepcopy(tool_response)
        modified_response["result"] = (
            f"{original_result} (Note: This is the capital of the USA. 🇺🇸)"
        )
        modified_response["note_added_by_callback"] = True
        return modified_response

    return None


# Create the Agent
root_agent = LlmAgent(
    name="tool_callback_agent",
    model="gemini-2.5-flash", # FIX: Updated to supported 2026 model version
    description="An agent that demonstrates tool callbacks by looking up capital cities",
    instruction="""
    You are a helpful geography assistant.
    
    Your job is to:
    - Find capital cities when asked using the get_capital_city tool.
    - Use the exact country name provided by the user.
    - ALWAYS return the EXACT result from the tool, without changing it.
    - When reporting a capital, display it EXACTLY as returned by the tool.
    """,
    tools=[get_capital_city],
    before_tool_callback=before_tool_callback,
    after_tool_callback=after_tool_callback,
)