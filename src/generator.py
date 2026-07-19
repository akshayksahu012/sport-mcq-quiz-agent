import json
import google.generativeai as genai
from src.config import GEMINI_API_KEY
from src.database import query_historic_facts
from src.search import get_live_news_context

# Configure the Gemini client once at import time
genai.configure(api_key=GEMINI_API_KEY)


def compile_quiz_data(sport, difficulty):
    """
    1. Gathers context from ChromaDB (Historical).
    2. Gathers context from DuckDuckGo (Live news).
    3. Blends them inside a grounded prompt.
    4. Connects to Gemini and generates the structured quiz as JSON.
    """
    # Create query to run against ChromaDB
    db_query = f"{sport} history cup championships rules records"
    db_matches = query_historic_facts(sport=sport, query_text=db_query, n_results=2)
    db_context = "\n".join(db_matches) if db_matches else "No offline historic data recorded."

    # Search the live web
    web_context = get_live_news_context(sport)

    # Combine historical and web contexts
    unified_context = f"=== HISTORICAL FACTS ===\n{db_context}\n\n=== LIVE INTERNET NEWS ===\n{web_context}"

    # System instruction stays conceptually the same, just handed to Gemini differently
    system_instruction = (
        "You are an expert sports quiz creator. Your job is to write multiple-choice quizzes "
        "relying strictly on the provided Context. Avoid hallucinations. Do not use facts not "
        "found in the Context below. If facts are scarce, make do with what you have, "
        "but keep details completely accurate to the text context.\n\n"
        f"CONTEXT DETAILS:\n{unified_context}"
    )

    user_prompt = (
        f"Generate exactly 3 unique multiple-choice questions for the sport: {sport}.\n"
        f"Difficulty target: {difficulty}.\n\n"
        "Return ONLY valid JSON (no markdown fences, no preamble, no extra text) matching "
        "exactly this schema:\n"
        "{\n"
        '  "questions": [\n'
        "    {\n"
        '      "question": "string",\n'
        '      "options": ["A. ...", "B. ...", "C. ...", "D. ..."],\n'
        '      "correct_option": "A",\n'
        '      "explanation": "string, quoting/grounded in the context details"\n'
        "    }\n"
        "  ]\n"
        "}"
    )

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_instruction,
    )

    response = model.generate_content(
        user_prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.7,
        ),
    )

    quiz_json_text = response.text.strip()

    # Safety net: some models occasionally wrap JSON in ```json fences despite instructions
    if quiz_json_text.startswith("```"):
        quiz_json_text = quiz_json_text.strip("`")
        if quiz_json_text.lower().startswith("json"):
            quiz_json_text = quiz_json_text[4:].strip()

    # Validate it's parseable before handing back to app.py (raises if malformed)
    json.loads(quiz_json_text)

    return quiz_json_text, unified_context