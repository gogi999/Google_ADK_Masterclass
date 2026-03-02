from datetime import datetime
from google.genai import types


# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


# ===============================
# STATE MANAGEMENT (ASYNC FIXED)
# ===============================

async def update_interaction_history(
    session_service, app_name, user_id, session_id, entry
):
    """Add an entry to the interaction history in state."""
    try:
        session = await session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )

        interaction_history = session.state.get("interaction_history", [])

        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        interaction_history.append(entry)

        session.state["interaction_history"] = interaction_history

    except Exception as e:
        print(f"Error updating interaction history: {e}")


async def add_user_query_to_history(
    session_service, app_name, user_id, session_id, query
):
    await update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {
            "action": "user_query",
            "query": query,
        },
    )


async def add_agent_response_to_history(
    session_service, app_name, user_id, session_id, agent_name, response
):
    await update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {
            "action": "agent_response",
            "agent": agent_name,
            "response": response,
        },
    )


# ===============================
# DISPLAY STATE (ASYNC FIXED)
# ===============================

async def display_state(
    session_service, app_name, user_id, session_id, label="Current State"
):
    try:
        session = await session_service.get_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
        )

        print(f"\n{'-' * 10} {label} {'-' * 10}")

        user_name = session.state.get("user_name", "Unknown")
        print(f"👤 User: {user_name}")

        purchased_courses = session.state.get("purchased_courses", [])
        if purchased_courses:
            print("📚 Courses:")
            for course in purchased_courses:
                print(f"  - {course}")
        else:
            print("📚 Courses: None")

        interaction_history = session.state.get("interaction_history", [])
        if interaction_history:
            print("📝 Interaction History:")
            for idx, interaction in enumerate(interaction_history, 1):
                action = interaction.get("action")
                timestamp = interaction.get("timestamp")

                if action == "user_query":
                    print(
                        f'  {idx}. User query at {timestamp}: "{interaction.get("query")}"'
                    )
                elif action == "agent_response":
                    print(
                        f'  {idx}. {interaction.get("agent")} response at {timestamp}: "{interaction.get("response")}"'
                    )
        else:
            print("📝 Interaction History: None")

        print("-" * (22 + len(label)))

    except Exception as e:
        print(f"Error displaying state: {e}")


# ===============================
# AGENT RESPONSE PROCESSING
# ===============================

async def process_agent_response(event):
    final_response = None

    if event.content and event.content.parts:
        for part in event.content.parts:
            if hasattr(part, "text") and part.text:
                print(part.text.strip())

    if event.is_final_response():
        if event.content and event.content.parts:
            final_response = event.content.parts[0].text.strip()

            print(
                f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}"
                "========== FINAL AGENT RESPONSE =========="
                f"{Colors.RESET}"
            )
            print(f"{Colors.CYAN}{final_response}{Colors.RESET}\n")

    return final_response


# ===============================
# MAIN AGENT CALL (ASYNC FIXED)
# ===============================

async def call_agent_async(runner, user_id, session_id, query):
    content = types.Content(role="user", parts=[types.Part(text=query)])

    print(
        f"\n{Colors.BG_GREEN}{Colors.BLACK}{Colors.BOLD}"
        f"--- Running Query: {query} ---"
        f"{Colors.RESET}"
    )

    final_response_text = None
    agent_name = None

    # ✅ MUST await now
    await display_state(
        runner.session_service,
        runner.app_name,
        user_id,
        session_id,
        "State BEFORE processing",
    )

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content,
        ):
            if event.author:
                agent_name = event.author

            response = await process_agent_response(event)
            if response:
                final_response_text = response

    except Exception as e:
        print(f"{Colors.BG_RED}{Colors.WHITE}ERROR: {e}{Colors.RESET}")

    if final_response_text and agent_name:
        await add_agent_response_to_history(
            runner.session_service,
            runner.app_name,
            user_id,
            session_id,
            agent_name,
            final_response_text,
        )

    # ✅ MUST await now
    await display_state(
        runner.session_service,
        runner.app_name,
        user_id,
        session_id,
        "State AFTER processing",
    )

    print(f"{Colors.YELLOW}{'-' * 30}{Colors.RESET}")
    return final_response_text