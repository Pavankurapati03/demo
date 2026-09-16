"""
Google Gemini LLM Service for Quantellix.AI Chatbot in Order Fulfillment.
Uses the official google-genai SDK.
"""
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# List of currently active models in order of preference
CANDIDATE_MODELS = [
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3-flash-preview",
    "gemini-3.1-flash-lite",
    "gemini-3.1-flash-lite-preview",
]

def get_gemini_api_key() -> str:
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key and not key.startswith("your_"):
        return key

    # Check .env directly so updates take effect immediately without server restart
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val and not val.startswith("your_"):
                            os.environ["GEMINI_API_KEY"] = val
                            return val
        except Exception:
            pass
    return ""

def call_gemini_chat(messages: List[Dict[str, str]], user_name: str = "User") -> str:
    """
    Sends conversation history to Gemini and returns the model response.
    Falls back gracefully if API key is not yet set or if any network error occurs.
    """
    api_key = get_gemini_api_key()
    if not api_key or api_key.startswith("your_") or api_key == "":
        return (
            f"Hello {user_name}! I am **Quantellix.AI**, your personal AI assistant for e-commerce order execution.\n\n"
            f"💡 **Tip:** To enable live responses powered by Google Gemini, please paste your API key from Google AI Studio "
            f"into your `.env` file as `GEMINI_API_KEY=...`.\n\n"
            f"You can also click **View Dashboards** at the top to inspect our 3 stages of Order Execution!"
        )

    system_instruction = (
        f"You are Quantellix.AI (powering Sriya AI), a world-class multi-modal AI assistant specializing in "
        f"E-Commerce Order Execution, Supply Chain Intelligence, and Predictive Analytics.\n"
        f"The user's first name is {user_name}.\n"
        f"Your domain knowledge covers:\n"
        f"1. Sales Demand Forecasting (Meta Prophet, LSTM, SARIMA, WMAPE error holdout evaluation).\n"
        f"2. S&OP Demand Planning (5 core business outcomes: Global Demand, Lead Time, Weighted List Price, Approved Vendors, Defect Rate, ROP).\n"
        f"3. Procurement Decision Engine (MCDA multi-criteria vendor scoring, MOQ & batching constraints, 5-point audit compliance, PO generation).\n"
        f"Tone & Style:\n"
        f"- Always address {user_name} respectfully and helpfully.\n"
        f"- Format answers cleanly with Markdown bullet points and bold highlights.\n"
        f"- Keep answers concise, highly intelligent, and direct."
    )

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key)

        # Build message history and determine latest user message
        history: List[types.Content] = []
        last_user_message = ""

        # Find the last user message
        last_user_idx = -1
        for idx in range(len(messages) - 1, -1, -1):
            if messages[idx].get("sender") == "user" and messages[idx].get("text", "").strip():
                last_user_idx = idx
                last_user_message = messages[idx].get("text", "").strip()
                break

        if last_user_idx != -1:
            for idx, m in enumerate(messages):
                if idx == last_user_idx:
                    continue
                role = "user" if m.get("sender") == "user" else "model"
                text = m.get("text", "")
                if text:
                    history.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))
        else:
            last_user_message = messages[-1].get("text", "Hello") if messages else "Hello"

        gen_config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.7,
            max_output_tokens=1024,
        )

        # Attempt with candidate models using chats.create (recommended by Google GenAI SDK)
        last_error = None
        for model in CANDIDATE_MODELS:
            try:
                chat = client.chats.create(
                    model=model,
                    history=history if history else None,
                    config=gen_config,
                )
                response = chat.send_message(last_user_message)
                if response and response.text:
                    return response.text
            except Exception as e_chat:
                logger.warning(f"chat.send_message failed on {model}: {e_chat}, trying generate_content fallback...")
                try:
                    # Fallback to generate_content with all contents
                    all_contents = []
                    for m in messages:
                        role = "user" if m.get("sender") == "user" else "model"
                        text = m.get("text", "")
                        if text:
                            all_contents.append(types.Content(role=role, parts=[types.Part.from_text(text=text)]))

                    response = client.models.generate_content(
                        model=model,
                        contents=all_contents,
                        config=gen_config,
                    )
                    if response and response.text:
                        return response.text
                except Exception as e_gen:
                    logger.warning(f"generate_content also failed on {model}: {e_gen}")
                    last_error = e_gen

        if last_error:
            raise last_error

        return "I received your message, but the model did not generate any text output. Please try again."

    except Exception as exc:
        logger.error(f"Error calling Gemini API: {exc}")
        return f"⚠️ **Gemini API Error:** {str(exc)}\n\nPlease ensure your `GEMINI_API_KEY` in `.env` is valid."
