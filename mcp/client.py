"""Minimal MCP client: launch the server over stdio, discover, then call."""
import asyncio, json, sys, pathlib
from mcp import Client
from mcp.client.stdio import StdioServerParameters
H = pathlib.Path(__file__).parent
async def main():
    params = StdioServerParameters(command=sys.executable, args=[str(H / "tap.py")])
    out = {}
    async with Client(params) as c:
        tools = await c.list_tools()
        out["tools"] = [{"name": t.name, "description": t.description, "inputSchema": t.input_schema} for t in tools.tools]
        out["resources"] = [str(r.uri) for r in (await c.list_resources()).resources]
        out["prompts"] = [p.name for p in (await c.list_prompts()).prompts]
        r = await c.call_tool("search_notes", {"query": "coffee"})
        out["call_search"] = [x.text for x in r.content]
        r = await c.call_tool("add_note", {"title": "travel", "text": "book train to Tahoe"})
        out["call_add"] = [x.text for x in r.content]
        rr = await c.read_resource("notes://all")
        out["resource_read"] = [x.text for x in rr.contents]
    print(json.dumps(out, indent=1))
    (H / "client-output.json").write_text(json.dumps(out, indent=1))
asyncio.run(main())
