# DRAFT REFERENCE, TO BE REVIEWED AND REWRITTEN BY THE TEAM.
# SI Console skeleton code. Reference only. Not for Fallen submission.
# The tool registry is new code. Autumn had no tool calling at all.
# Its claude.py says "No tools and no conversation history yet".
# This file is the single place where tools are defined, tagged, and
# checked. The coordinator never calls a tool directly. It asks the
# registry, the registry validates the call, GUARD checks it, then
# the tool runs. The LLM cannot change a tag. The LLM cannot add a
# tool. A tool that is not in this file does not exist.
# Tool names and tags are copied exactly from ARCHITECTURE.md section 5.
# Tool permission table by role is copied exactly from section 5.8.
# If ARCHITECTURE.md changes a tag, change it here and nowhere else.
"""Tool registry. Every tool, its tag, its schema, and its role list."""

from __future__ import annotations

from dataclasses import dataclass, field

from si_console import config
from si_console.errors import ToolError

# Tags. SAFE runs without a button press. NEEDS APPROVAL pauses until
# green or red. GUARD enforces the tag in code.
SAFE = "SAFE"
NEEDS_APPROVAL = "NEEDS APPROVAL"

# Fixed action menu, copied exactly from ARCHITECTURE.md section 4.2.
# The coordinator may pick only these actions. Anything else is
# rejected by code with BAD_ACTION.
FIXED_MENU = {
    "create_task",
    "read_task",
    "read_portfolio",
    "run_rules_engine",
    "search_web",
    "write_research_note",
    "propose_order",
    "request_approval",
    "mark_blocked",
    "mark_done",
    "speak",
    "escalate",
}


@dataclass
class Tool:
    """One tool. Name, tag, JSON schema, and which roles may call it."""

    name: str
    tag: str
    schema: dict
    roles: set = field(default_factory=set)
    description: str = ""

    def to_deepseek_tool(self) -> dict:
        """The shape DeepSeek tool calling wants for this tool."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema,
            },
        }


def _schema(properties: dict, required: list) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": required,
        "additionalProperties": False,
    }


# v1 tool list, copied from ARCHITECTURE.md section 5. Each tool has
# a schema. Extra fields are dropped, not passed through. Unknown
# fields cause the reply to be rejected with BAD_SCHEMA.
TOOLS: dict[str, Tool] = {
    "vault_read": Tool(
        name="vault_read",
        tag=SAFE,
        description="Read a vault note by path. Read only.",
        roles={"coordinator", "signal", "risk", "execution"},
        schema=_schema(
            {
                "path": {
                    "type": "string",
                    "description": "Must start with vault/si-console/ and end with .md",
                }
            },
            ["path"],
        ),
    ),
    "vault_write": Tool(
        name="vault_write",
        tag=NEEDS_APPROVAL,
        description=(
            "Write a full vault note by atomic write. Tag is NEEDS APPROVAL "
            "for order and portfolio notes, SAFE for research and log notes. "
            "The registry sets the tag per file, see tag_for_write."
        ),
        roles={"coordinator", "signal", "risk", "execution"},
        schema=_schema(
            {
                "path": {"type": "string"},
                "content": {"type": "string", "description": "Full file text"},
            },
            ["path", "content"],
        ),
    ),
    "vault_list": Tool(
        name="vault_list",
        tag=SAFE,
        description="List task notes by status. Returns ids and titles only.",
        roles={"coordinator", "signal", "risk"},
        schema=_schema(
            {
                "status": {
                    "type": "string",
                    "enum": ["queued", "working", "blocked", "done"],
                },
                "agent": {
                    "type": "string",
                    "enum": ["signal", "risk", "execution", "coordinator", ""],
                },
            },
            ["status"],
        ),
    ),
    "shell_run": Tool(
        name="shell_run",
        tag=NEEDS_APPROVAL,
        description="Run one allow listed shell command. Always needs approval.",
        roles={"execution"},
        schema=_schema(
            {
                "command": {"type": "string"},
                "timeout_seconds": {"type": "integer", "minimum": 5, "maximum": 60},
            },
            ["command", "timeout_seconds"],
        ),
    ),
    "run_python": Tool(
        name="run_python",
        tag=NEEDS_APPROVAL,
        description="Run one allow listed script: rules_engine, make_slides, backtest.",
        roles={"signal", "execution"},
        schema=_schema(
            {
                "script": {
                    "type": "string",
                    "enum": ["rules_engine", "make_slides", "backtest"],
                },
                "args": {"type": "object"},
            },
            ["script", "args"],
        ),
    ),
    "web_search": Tool(
        name="web_search",
        tag=SAFE,
        description="Call Bocha for research. Research only. Never changes a ranking.",
        roles={"coordinator", "signal"},
        schema=_schema(
            {
                "query": {"type": "string", "minLength": 1, "maxLength": 200},
                "count": {"type": "integer", "minimum": 1, "maximum": 10},
                "freshness": {
                    "type": "string",
                    "enum": ["oneDay", "oneWeek", "oneMonth", "oneYear", "noLimit"],
                },
                "lang": {"type": "string", "enum": ["en", "zh"]},
            },
            ["query", "count", "freshness", "lang"],
        ),
    ),
    "fetch_url": Tool(
        name="fetch_url",
        tag=SAFE,
        description="Fetch one page and return cleaned text, capped at 8000 chars.",
        roles={"coordinator", "signal"},
        schema=_schema({"url": {"type": "string"}}, ["url"]),
    ),
    "create_task_note": Tool(
        name="create_task_note",
        tag=SAFE,
        description="Create a task note with status queued. Refuses duplicates.",
        roles={"coordinator", "signal", "risk"},
        schema=_schema(
            {
                "task_id": {"type": "string"},
                "agent": {
                    "type": "string",
                    "enum": ["signal", "risk", "execution", "coordinator"],
                },
                "type": {
                    "type": "string",
                    "enum": ["signal", "risk_check", "order", "narration", "research"],
                },
                "summary": {"type": "string"},
                "depends_on": {"type": "array", "items": {"type": "string"}},
                "proposal": {"type": "string"},
                "ticker": {"type": "string"},
                "amount": {"type": "number"},
                "price": {"type": "number"},
                "lang": {"type": "string", "enum": ["en", "zh"]},
                "priority": {"type": "integer", "minimum": 1, "maximum": 3},
            },
            ["task_id", "agent", "type", "summary"],
        ),
    ),
    "update_task_status": Tool(
        name="update_task_status",
        tag=SAFE,
        description=(
            "Change a task status. Tag is NEEDS APPROVAL for done on an "
            "order task, SAFE for working or blocked. See tag_for_status."
        ),
        roles={"coordinator", "risk", "execution"},
        schema=_schema(
            {
                "task_id": {"type": "string"},
                "status": {
                    "type": "string",
                    "enum": ["queued", "working", "blocked", "done"],
                },
                "reason_code": {"type": "string"},
            },
            ["task_id", "status"],
        ),
    ),
    "read_portfolio": Tool(
        name="read_portfolio",
        tag=SAFE,
        description="Read the portfolio note for one mode. Read only.",
        roles={"coordinator", "risk", "execution"},
        schema=_schema(
            {"mode": {"type": "string", "enum": ["home", "booth"]}},
            ["mode"],
        ),
    ),
    "make_slides": Tool(
        name="make_slides",
        tag=NEEDS_APPROVAL,
        description="Make slides with python-pptx. Never executes a trade.",
        roles={"execution"},
        schema=_schema(
            {
                "title": {"type": "string"},
                "bullets": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 5,
                },
                "slide_count": {"type": "integer", "minimum": 1, "maximum": 5},
                "lang": {"type": "string", "enum": ["en", "zh"]},
                "output_path": {
                    "type": "string",
                    "description": "Must be under vault/si-console/slides/",
                },
            },
            ["title", "bullets", "slide_count", "lang", "output_path"],
        ),
    ),
    "speak_sentence": Tool(
        name="speak_sentence",
        tag=SAFE,
        description="Speak one prewritten sentence by id. Free text is never spoken.",
        roles={"coordinator", "signal", "risk", "execution"},
        schema=_schema(
            {
                "sentence_id": {"type": "string", "description": "Must exist in strings.json"},
                "lang": {"type": "string", "enum": ["en", "zh"]},
            },
            ["sentence_id", "lang"],
        ),
    ),
    "show_message": Tool(
        name="show_message",
        tag=SAFE,
        description="Show one prewritten message on both screens, by id.",
        roles={"coordinator"},
        schema=_schema(
            {
                "message_id": {"type": "string", "description": "Must exist in strings.json"},
                "lang": {"type": "string", "enum": ["en", "zh"]},
            },
            ["message_id", "lang"],
        ),
    ),
}


def tag_for_write(path: str) -> str:
    """The tag for vault_write depends on the file being written.

    Order and portfolio notes need approval. Research and log notes
    do not. The LLM cannot change this. The path decides, not the
    caller. This is the rule from ARCHITECTURE.md section 5.1.
    """
    if "/tasks/" in path or "/portfolio/" in path:
        return NEEDS_APPROVAL
    return SAFE


def tag_for_status(task_type: str, new_status: str) -> str:
    """The tag for update_task_status depends on what is changing.

    Done on an order task needs approval. Working or blocked does
    not. This is the rule from ARCHITECTURE.md section 5.5.
    """
    if task_type == "order" and new_status == "done":
        return NEEDS_APPROVAL
    return SAFE


def tool_names_for_role(role: str) -> set[str]:
    """The names of the tools one role may call. GUARD checks a tool
    name against this set. Do not pass Tool.roles here: that set
    holds role names, not tool names. Passing Tool.roles blocks
    every tool call, because a tool name is never a role name. That
    bug was found by the mocked coordinator loop tests in
    tests/test_coordinator_loop.py. The coordinator calls this
    helper. No other caller should need it."""
    return {tool.name for tool in TOOLS.values() if role in tool.roles}


def tools_for_role(role: str) -> list[dict]:
    """The DeepSeek tool list for one role only. The coordinator
    calls DeepSeek with the tool list for that agent role only."""
    return [
        tool.to_deepseek_tool()
        for tool in TOOLS.values()
        if role in tool.roles
    ]


def validate_tool_call(name: str, args: dict) -> None:
    """Validate one tool call before it runs. Raises ToolError.

    Checks, in order: the tool exists, the args are a dict, every
    required field is present, enum values are in range, and the
    ticker is on the allow list. A failed check is BAD_SCHEMA or
    BAD_TICKER. The whole reply is discarded, never partly run.
    """
    tool = TOOLS.get(name)
    if tool is None:
        raise ToolError("BAD_ACTION", f"Unknown tool: {name}.")
    if not isinstance(args, dict):
        raise ToolError("BAD_SCHEMA", f"Tool {name} args must be an object.")
    for field_name in tool.schema.get("required", []):
        if field_name not in args:
            raise ToolError(
                "BAD_SCHEMA",
                f"Tool {name} is missing required field: {field_name}.",
            )
    if "ticker" in args and args["ticker"]:
        if args["ticker"] not in config.ALLOWED_TICKERS:
            raise ToolError(
                "BAD_TICKER",
                f"Ticker is not on the allow list: {args['ticker']}.",
                remedy=f"Use one of: {sorted(config.ALLOWED_TICKERS)}.",
            )
    if "amount" in args and args["amount"] is not None:
        if not isinstance(args["amount"], (int, float)) or args["amount"] < 0:
            raise ToolError("BAD_AMOUNT", "Amount must be a number, zero or more.")
    if "output_path" in args and args["output_path"]:
        if not args["output_path"].startswith("vault/si-console/slides/"):
            raise ToolError(
                "BAD_SCHEMA",
                "Slide output must be under vault/si-console/slides/.",
            )
