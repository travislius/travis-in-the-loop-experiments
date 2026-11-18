"""tiny-notes: a minimal local MCP server (Travis in the Loop, MCP Explained).
One tool, one resource, one prompt. Runs over stdio.
"""
from mcp.server import MCPServer

app = MCPServer("tiny-notes")
NOTES = {"groceries": "eggs, oat milk, coffee", "ideas": "video about MCP", "wifi": "home wifi password: hunter2 (FAKE test secret)"}

@app.tool()
def search_notes(query: str) -> str:
    """Search my notes by keyword and return matching notes."""
    hits = [f"{k}: {v}" for k, v in NOTES.items() if query.lower() in (k + " " + v).lower()]
    return "\n".join(hits) or "no matching notes"

@app.tool()
def add_note(title: str, text: str) -> str:
    """Save a new note."""
    NOTES[title] = text
    return f"saved '{title}' ({len(NOTES)} notes total)"

@app.resource("notes://all")
def all_notes() -> str:
    """Every note, as plain text (read-only context)."""
    return "\n".join(f"{k}: {v}" for k, v in NOTES.items())

@app.prompt()
def weekly_review() -> str:
    """A reusable prompt template the user can pick from a menu."""
    return "Read notes://all and write a 3-bullet weekly review of my notes."

if __name__ == "__main__":
    app.run()  # stdio transport
