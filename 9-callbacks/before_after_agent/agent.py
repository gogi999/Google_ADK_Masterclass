"""
Before and After Agent Callbacks Example
Fixed version – JSON-safe for persistent storage
"""

from datetime import datetime
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.genai import types


# ==============================
# BEFORE CALLBACK
# ==============================

def before_agent_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """
    Logs when the agent starts processing a request.
    Ensures session state is JSON-serializable.
    """

    state = callback_context.state

    # Always use ISO string for persistence safety
    timestamp = datetime.now()
    timestamp_str = timestamp.isoformat()

    # Set agent name if not present
    if "agent_name" not in state:
        state["agent_name"] = "SimpleChatBot"

    # Initialize or increment request counter
    if "request_counter" not in state:
        state["request_counter"] = 1
    else:
        state["request_counter"] += 1

    # Store start time as ISO string (JSON safe)
    state["request_start_time"] = timestamp_str

    print("=== AGENT EXECUTION STARTED ===")
    print(f"Request #: {state['request_counter']}")
    print(f"Timestamp: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(
        f"\n[BEFORE CALLBACK] Agent processing request #{state['request_counter']}"
    )

    return None


# ==============================
# AFTER CALLBACK
# ==============================

def after_agent_callback(
    callback_context: CallbackContext,
) -> Optional[types.Content]:
    """
    Logs when the agent finishes processing a request.
    Handles ISO datetime string correctly.
    """

    state = callback_context.state

    timestamp = datetime.now()
    duration = None

    # Convert stored ISO string back to datetime safely
    if "request_start_time" in state:
        try:
            start_time = datetime.fromisoformat(
                state["request_start_time"]
            )
            duration = (timestamp - start_time).total_seconds()
        except Exception:
            duration = None  # Failsafe

    print("=== AGENT EXECUTION COMPLETED ===")
    print(f"Request #: {state.get('request_counter', 'Unknown')}")

    if duration is not None:
        print(f"Duration: {duration:.2f} seconds")

    print(
        f"[AFTER CALLBACK] Agent completed request #{state.get('request_counter', 'Unknown')}"
    )

    if duration is not None:
        print(
            f"[AFTER CALLBACK] Processing took {duration:.2f} seconds"
        )

    return None


# ==============================
# AGENT DEFINITION
# ==============================

root_agent = LlmAgent(
    name="before_after_agent",
    model="gemini-2.5-flash",  # Updated model (no deprecated versions)
    description="A basic agent that demonstrates before and after agent callbacks",
    instruction="""
    You are a friendly greeting agent. Your name is {agent_name}.
    
    Your job is to:
    - Greet users politely
    - Respond to basic questions
    - Keep your responses friendly and concise
    """,
    before_agent_callback=before_agent_callback,
    after_agent_callback=after_agent_callback,
)