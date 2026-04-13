"""
AI-powered music recommender using RAG + Agentic Workflow.

The agent uses Claude with tool use to:
1. Interpret natural language user requests
2. Retrieve matching songs via the existing scoring engine (RAG retrieval step)
3. Generate a natural language response grounded in the retrieved data

Run via: python src/main.py --ai
"""

import json
import logging
from typing import Dict, List

import anthropic

try:
    from recommender import recommend_songs
except ModuleNotFoundError:
    from src.recommender import recommend_songs

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a music recommendation assistant. Your catalog contains songs with specific "
    "genres, moods, and energy levels. When the user asks for recommendations, call "
    "get_song_recommendations with appropriate parameters. If the user mentions a genre "
    "or mood that might not exist in the catalog, first call get_catalog_info to check "
    "what is available and inform the user accordingly. "
    "Always base your response on the actual songs returned by the tool — never invent "
    "song titles or artists. Keep responses concise (2-4 sentences plus the song list)."
)

# ---------------------------------------------------------------------------
# Tool schemas
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "get_song_recommendations",
        "description": (
            "Retrieve the top matching songs from the catalog using the existing scoring "
            "logic. Call this when the user wants song recommendations. Energy should be "
            "a float from 0.0 (very calm) to 1.0 (very intense). All parameters are "
            "optional — omit ones the user did not specify."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "genre": {
                    "type": "string",
                    "description": (
                        "Preferred genre, e.g. pop, lofi, rock, ambient, jazz, "
                        "synthwave, indie pop"
                    ),
                },
                "mood": {
                    "type": "string",
                    "description": (
                        "Preferred mood, e.g. happy, chill, intense, relaxed, moody, focused"
                    ),
                },
                "energy": {
                    "type": "number",
                    "description": "Target energy level as a float between 0.0 and 1.0",
                },
                "k": {
                    "type": "integer",
                    "description": "Number of songs to return. Defaults to 5.",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_catalog_info",
        "description": (
            "Returns the list of available genres, moods, and the energy range in the "
            "song catalog. Call this before get_song_recommendations if you are unsure "
            "whether a requested genre or mood exists in the catalog."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
]

# ---------------------------------------------------------------------------
# Catalog helpers
# ---------------------------------------------------------------------------


def build_catalog_index(songs: List[Dict]) -> Dict:
    """Build an index of available genres, moods, and energy range from the song list."""
    genres = sorted({s["genre"] for s in songs if s.get("genre")})
    moods = sorted({s["mood"] for s in songs if s.get("mood")})
    energies = [s["energy"] for s in songs if s.get("energy") is not None]
    energy_range = [min(energies), max(energies)] if energies else [0.0, 1.0]
    return {"genres": genres, "moods": moods, "energy_range": energy_range}


# ---------------------------------------------------------------------------
# Tool handlers
# ---------------------------------------------------------------------------


def handle_get_catalog_info(songs: List[Dict]) -> str:
    """Return catalog metadata as a JSON string."""
    index = build_catalog_index(songs)
    logger.debug("Catalog info requested: %s", index)
    return json.dumps(index)


def handle_get_song_recommendations(tool_input: Dict, songs: List[Dict]) -> str:
    """
    Retrieve top songs matching the requested genre/mood/energy.

    Guardrails:
    - Energy is clamped to [0.0, 1.0]; a WARNING is logged if clamping occurs.
    - Unknown genre or mood returns a warning with the available values.
    - Empty result set is flagged with a warning message.
    """
    index = build_catalog_index(songs)

    genre = tool_input.get("genre")
    mood = tool_input.get("mood")
    energy = tool_input.get("energy", 0.5)
    k = tool_input.get("k", 5)

    # Guardrail: clamp energy
    if energy < 0.0 or energy > 1.0:
        logger.warning(
            "Energy value %s out of range [0, 1]; clamping.", energy
        )
        energy = max(0.0, min(1.0, float(energy)))

    # Guardrail: unknown genre
    if genre and genre not in index["genres"]:
        logger.warning("Unknown genre requested: '%s'", genre)
        return json.dumps(
            {
                "warning": f"Genre '{genre}' not found in catalog.",
                "available_genres": index["genres"],
                "songs": [],
            }
        )

    # Guardrail: unknown mood
    if mood and mood not in index["moods"]:
        logger.warning("Unknown mood requested: '%s'", mood)
        return json.dumps(
            {
                "warning": f"Mood '{mood}' not found in catalog.",
                "available_moods": index["moods"],
                "songs": [],
            }
        )

    user_prefs = {
        "genre": genre or "",
        "mood": mood or "",
        "energy": energy,
    }

    results = recommend_songs(user_prefs, songs, k=k)
    logger.info(
        "get_song_recommendations returned %d result(s) for prefs: %s",
        len(results),
        user_prefs,
    )

    if not results:
        logger.warning("No songs returned for prefs: %s", user_prefs)
        return json.dumps(
            {"songs": [], "message": "No results returned. Try different parameters."}
        )

    songs_out = []
    for song, score, explanation in results:
        songs_out.append(
            {
                "title": song["title"],
                "artist": song["artist"],
                "genre": song["genre"],
                "mood": song["mood"],
                "energy": song["energy"],
                "score": round(score, 2),
                "confidence_pct": round(score / 6.0 * 100, 1),
                "explanation": explanation,
            }
        )

    return json.dumps({"songs": songs_out, "count": len(songs_out)})


# ---------------------------------------------------------------------------
# Tool dispatcher
# ---------------------------------------------------------------------------


def execute_tool(name: str, tool_input: Dict, songs: List[Dict]) -> str:
    """Dispatch a tool call by name and return the result as a JSON string."""
    logger.info("Tool called: %s | input: %s", name, tool_input)

    if name == "get_song_recommendations":
        return handle_get_song_recommendations(tool_input, songs)
    if name == "get_catalog_info":
        return handle_get_catalog_info(songs)

    logger.warning("Unknown tool name requested: '%s'", name)
    return json.dumps({"error": f"Unknown tool: '{name}'"})


# ---------------------------------------------------------------------------
# Agentic session loop
# ---------------------------------------------------------------------------


def run_ai_session(songs: List[Dict], client: anthropic.Anthropic) -> None:
    """
    Run an interactive conversational session.

    The loop accepts natural language input, sends it to Claude with tool
    definitions, processes any tool calls (retrieving songs via the existing
    scoring engine), and prints the final AI-generated response.

    Type 'quit' or 'exit' to end the session.
    """
    logger.info("AI session started with %d songs in catalog.", len(songs))
    print("\nAI Music Recommender — type 'quit' to exit")
    print("=" * 50)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit"}:
            logger.info("Session ended by user.")
            print("Goodbye!")
            break

        logger.info("User query: %s", user_input[:200])

        messages = [{"role": "user", "content": user_input}]

        try:
            while True:
                response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=1024,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=messages,
                )

                logger.debug(
                    "Claude response: stop_reason=%s", response.stop_reason
                )

                if response.stop_reason == "end_turn":
                    # Print the final text response
                    for block in response.content:
                        if hasattr(block, "text"):
                            print(f"\nAssistant: {block.text}")
                    break

                if response.stop_reason == "tool_use":
                    # Append Claude's message (which contains tool_use blocks)
                    messages.append(
                        {"role": "assistant", "content": response.content}
                    )

                    # Process each tool call and collect results
                    tool_results = []
                    for block in response.content:
                        if block.type == "tool_use":
                            result_str = execute_tool(
                                block.name, block.input, songs
                            )
                            tool_results.append(
                                {
                                    "type": "tool_result",
                                    "tool_use_id": block.id,
                                    "content": result_str,
                                }
                            )

                    messages.append(
                        {"role": "user", "content": tool_results}
                    )
                    # Continue the agentic loop

        except anthropic.AuthenticationError as exc:
            logger.error("Authentication error: %s", exc)
            print(
                "\nError: Invalid API key. Check that ANTHROPIC_API_KEY is set correctly."
            )
            break
        except anthropic.APIConnectionError as exc:
            logger.error("Connection error: %s", exc)
            print("\nError: Could not connect to the Anthropic API. Check your network.")
        except anthropic.APIError as exc:
            logger.error("Unexpected API error: %s", exc)
            print(f"\nError: API request failed ({exc}). Please try again.")
