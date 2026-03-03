"""
Before and After Model Callbacks Example

This example demonstrates using model callbacks 
to filter content and log model interactions.
"""

import copy
from datetime import datetime
from typing import Optional

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types


def before_model_callback(
    callback_context: CallbackContext, llm_request: LlmRequest
) -> Optional[LlmResponse]:
    """
    Runs before the model processes a request to filter content and log info.
    """
    state = callback_context.state
    agent_name = callback_context.agent_name

    # Extract the last user message safely
    last_user_message = ""
    if llm_request.contents:
        for content in reversed(llm_request.contents):
            if content.role == "user" and content.parts:
                text_parts = [p.text for p in content.parts if hasattr(p, "text") and p.text]
                if text_parts:
                    last_user_message = " ".join(text_parts)
                    break

    # Log the request details
    print(f"\n--- [AGENT: {agent_name}] REQUEST STARTED ---")
    if last_user_message:
        print(f"User message snippet: {last_user_message[:75]}...")
        state["last_user_message"] = last_user_message
    else:
        print("User message: <empty or non-text>")

    print(f"Timestamp: {datetime.now().strftime('%H:%M:%S')}")

    # Safety Filter: Check for prohibited words
    prohibited_words = ["sucks", "terrible"] 
    if last_user_message and any(word in last_user_message.lower() for word in prohibited_words):
        print("⚠️  BLOCKING: Inappropriate content detected.")
        
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[
                    types.Part(
                        text="I'm here to help, but I cannot respond to messages containing that language. "
                        "Could you please rephrase your request?"
                    )
                ],
            )
        )

    # FIX: Record start time as a string to prevent JSON serialization errors in SQLite
    state["model_start_time"] = datetime.now().isoformat()
    print("✅ Request approved for LLM processing")
    return None


def after_model_callback(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> Optional[LlmResponse]:
    """
    Post-processes the model response to refine tone/vocabulary.
    """
    print("--- PROCESSING RESPONSE ---")

    if not llm_response or not llm_response.content or not llm_response.content.parts:
        return None

    # Simple dictionary for euphemisms/refinement
    replacements = {
        "problem": "challenge",
        "difficult": "complex",
        "bad": "suboptimal"
    }

    modified = False
    new_parts = []

    for part in llm_response.content.parts:
        if hasattr(part, "text") and part.text:
            original_text = part.text
            modified_text = original_text
            
            for word, sub in replacements.items():
                if word in modified_text.lower():
                    # Replace lowercase
                    modified_text = modified_text.replace(word, sub)
                    # Replace Capitalized
                    modified_text = modified_text.replace(word.capitalize(), sub.capitalize())
                    modified = True
            
            new_parts.append(types.Part(text=modified_text))
        else:
            new_parts.append(copy.deepcopy(part))

    if modified:
        print("↺ Tone refinement applied to response.")
        return LlmResponse(content=types.Content(role="model", parts=new_parts))

    print("✓ Response passed through without changes.")
    return None


# Create the Agent
root_agent = LlmAgent(
    name="content_filter_agent",
    model="gemini-2.5-flash", # UPDATED: Moved to the current 2026 model version
    description="An agent that demonstrates model callbacks for content filtering and logging",
    instruction="""
    You are a helpful assistant.
    - Answer user questions concisely and factually.
    - Maintain a professional and friendly tone.
    """,
    before_model_callback=before_model_callback,
    after_model_callback=after_model_callback,
)
