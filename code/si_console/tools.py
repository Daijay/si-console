# This file is the single place where tools are defined, tagged, and
# checked. The coordinator never calls a tool directly. It asks the
# registry, the registry validates the call, GUARD checks it, then
# the tool runs. The LLM cannot change a tag. The LLM cannot add a
# tool. A tool that is not in this file does not exist. One list means
# there is only one place to review what an agent is able to do.
# Each tool's tag and each role's permission table are defined here and
# nowhere else.
"""Tool registry. Every tool, its tag, its schema, and its role list."""

from __future__ import annotations

import math
import posixpath
from dataclasses import dataclass, field

from si_console import config
from si_console.errors import ToolError

# Tags. SAFE runs without a button press. NEEDS APPROVAL pauses until
# green or red. GUARD enforces the tag in code.
SAFE = "SAFE"
NEEDS_APPROVAL = "NEEDS APPROVAL"

# Fixed action menu.
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


# v1 tool list. Each tool has
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
        description="Web search for research (Zhipu, Bocha fallback). Research only. Never changes a ranking.",
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
    caller, so a model cannot talk its way past approval.
    """
    # Fail closed: only a path that is clearly a research or log note
    # is SAFE. "tasks/x.md" with no leading slash, "./tasks/x.md", or
    # an odd path all need approval.
    parts = [p for p in posixpath.normpath(str(path).replace("\\", "/")).split("/") if p]
    if "tasks" in parts or "portfolio" in parts or ".." in parts:
        return NEEDS_APPROVAL
    if "research" in parts or "log" in parts:
        return SAFE
    return NEEDS_APPROVAL


def tag_for_status(task_type: str, new_status: str) -> str:
    """The tag for update_task_status depends on what is changing.

    Done on an order task needs approval. Working or blocked does
    not, because only closing an order has a real effect.
    """
    if task_type == "order" and new_status == "done":
        return NEEDS_APPROVAL
    return SAFE


def effective_tag(name: str, args: dict) -> str:
    """The tag GUARD must use for one concrete call.

    The registry tag is the floor: a NEEDS APPROVAL tool never drops
    to SAFE. update_task_status is SAFE in the registry, but done on
    an order task needs approval (tag_for_status). The order type is
    read from the target task note, not from the caller. If the note
    cannot be read, fail closed and ask for approval.
    """
    tool = TOOLS[name]
    if tool.tag == NEEDS_APPROVAL:
        return NEEDS_APPROVAL
    if name == "update_task_status":
        from si_console.vault import read_note  # local: vault imports config only

        try:
            target_type = read_note(args.get("task_id", "")).type
        except Exception:
            return NEEDS_APPROVAL
        return tag_for_status(target_type, args.get("status", ""))
    return tool.tag


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
    properties = tool.schema.get("properties", {})
    if tool.schema.get("additionalProperties") is False:
        extra = sorted(set(args) - set(properties))
        if extra:
            raise ToolError(
                "BAD_SCHEMA", f"Tool {name} got unknown field(s): {', '.join(extra)}."
            )
    # The amount check runs before the generic type check so a bad
    # amount keeps its own reason code, BAD_AMOUNT.
    if "amount" in args and args["amount"] is not None:
        amount = args["amount"]
        if (
            isinstance(amount, bool)
            or not isinstance(amount, (int, float))
            or not math.isfinite(amount)
            or amount < 0
        ):
            raise ToolError("BAD_AMOUNT", "Amount must be a finite number, zero or more.")
    for field_name, value in args.items():
        _check_field(name, field_name, value, properties.get(field_name, {}))
    if "ticker" in args and args["ticker"]:
        if args["ticker"] not in config.ALLOWED_TICKERS:
            raise ToolError(
                "BAD_TICKER",
                f"Ticker is not on the allow list: {args['ticker']}.",
                remedy=f"Use one of: {sorted(config.ALLOWED_TICKERS)}.",
            )
    if "output_path" in args and args["output_path"]:
        if not is_slide_path(args["output_path"]):
            raise ToolError(
                "BAD_SCHEMA",
                "Slide output must be under vault/si-console/slides/.",
            )


SLIDES_PREFIX = "vault/si-console/slides/"


def is_slide_path(path: str) -> bool:
    """True when `path` stays inside vault/si-console/slides/ after
    normalising. A plain prefix check lets slides/../../x escape."""
    if not isinstance(path, str) or "\\" in path or not path.startswith(SLIDES_PREFIX):
        return False
    normal = posixpath.normpath(path)
    return normal.startswith(SLIDES_PREFIX) and normal != SLIDES_PREFIX.rstrip("/")


_JSON_TYPES = {
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "array": (list,),
    "object": (dict,),
    "boolean": (bool,),
}


def _check_field(tool_name: str, field_name: str, value, spec: dict) -> None:
    """Check one argument against its schema entry: type, enum, and
    the min and max bounds the registry declares. Raises BAD_SCHEMA."""

    def bad(why: str) -> ToolError:
        return ToolError("BAD_SCHEMA", f"Tool {tool_name} field {field_name}: {why}.")

    kind = spec.get("type")
    if kind:
        allowed = _JSON_TYPES.get(kind, (object,))
        # bool is an int in Python, but never a valid JSON number here.
        if (isinstance(value, bool) and kind != "boolean") or not isinstance(value, allowed):
            raise bad(f"must be {kind}")
    if "enum" in spec and value not in spec["enum"]:
        raise bad(f"must be one of {spec['enum']}")
    if isinstance(value, str):
        if "minLength" in spec and len(value) < spec["minLength"]:
            raise bad(f"shorter than {spec['minLength']}")
        if "maxLength" in spec and len(value) > spec["maxLength"]:
            raise bad(f"longer than {spec['maxLength']}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in spec and value < spec["minimum"]:
            raise bad(f"below {spec['minimum']}")
        if "maximum" in spec and value > spec["maximum"]:
            raise bad(f"above {spec['maximum']}")
    if isinstance(value, list):
        if "maxItems" in spec and len(value) > spec["maxItems"]:
            raise bad(f"more than {spec['maxItems']} items")
        item_spec = spec.get("items") or {}
        for item in value:
            _check_field(tool_name, field_name + "[]", item, item_spec)
