#!/usr/bin/env python3
"""Generate the Cursor plugin files from the Claude Code plugin files.

Source of truth (edit these):
  .claude-plugin/plugin.json, .claude-plugin/marketplace.json, .mcp.json, agents/*.md

Generated (never edit by hand):
  .cursor-plugin/plugin.json, .cursor-plugin/marketplace.json, .cursor-plugin/agents/*.md

The generated agents rewrite Claude `Skill` tool calls. Marketplace entries keep only
name, source, and description, which is what the Cursor schema allows.

Usage:
  python3 scripts/sync_cursor.py          # write the generated files
  python3 scripts/sync_cursor.py --check  # exit 1 when the generated files are stale
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLAUDE_DIR = ROOT / ".claude-plugin"
CURSOR_DIR = ROOT / ".cursor-plugin"
AGENTS_DIR = ROOT / "agents"
CURSOR_AGENTS_DIR = CURSOR_DIR / "agents"

REPOSITORY = "https://github.com/andrewhenriquef/personal-claude-plugin"
LICENSE = "MIT"

# Claude Code model alias -> Cursor `model` value. Cursor accepts `inherit`, `fast`,
# or a full model ID such as `claude-opus-5[effort=high]`.
MODEL_MAP = {"opus": "inherit", "sonnet": "inherit", "haiku": "fast"}
DEFAULT_MODEL = "inherit"

# An agent is readonly in Cursor when its Claude `tools` list has none of these.
WRITE_TOOLS = {"Write", "Edit", "Bash"}

# Claude Code calls skills through the `Skill` tool. Cursor agents have no such tool,
# so the generated copy rewrites those calls. Leftovers fail the sync.
SKILL_CALL = re.compile(r"Skill\(|`Skill` tool")
SKILL_INVOCATION = re.compile(
    r"(?P<verb>[Nn]ever call|[Cc]all|use) "
    r"`Skill\(skill:\s*\"(?P<name>[^\"]+)\""
    r"(?:,\s*(?:args:\s*)?(?P<args><[^>]*>|\.\.\.))?\)`"
)
CLAUDE_SKILL_PREFIX = (
    " Plugin skills may carry a prefix (`andrew-skills:security-analysis`). "
    "If the plain name is not found, use the name from the skills list."
)

ENV_DEFAULT = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*):-[^}]*\}")


def load_json(path):
    return json.loads(path.read_text())


def dump_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def cursor_mcp_servers(mcp):
    """Drop `type` and rewrite `${VAR:-default}` to `${VAR}`; return servers and variable names."""
    variables = []

    def rewrite(value):
        if isinstance(value, dict):
            return {k: rewrite(v) for k, v in value.items()}
        if isinstance(value, list):
            return [rewrite(v) for v in value]
        if isinstance(value, str):
            for name in ENV_DEFAULT.findall(value):
                if name not in variables:
                    variables.append(name)
            return ENV_DEFAULT.sub(r"${\1}", value)
        return value

    servers = {}
    for name, server in mcp.get("mcpServers", {}).items():
        servers[name] = rewrite({k: v for k, v in server.items() if k != "type"})
    return servers, variables


def build_plugin(claude_plugin, mcp):
    for skill in claude_plugin["skills"]:
        if not (ROOT / skill / "SKILL.md").is_file():
            sys.exit(f"error: {skill}/SKILL.md not found")

    plugin = {
        "name": claude_plugin["name"],
        "description": claude_plugin["description"],
        "version": claude_plugin["version"],
        "author": claude_plugin["author"],
        "repository": REPOSITORY,
        "license": LICENSE,
        "keywords": claude_plugin["keywords"],
        "skills": claude_plugin["skills"],
        "agents": "./.cursor-plugin/agents/",
    }

    servers, variables = cursor_mcp_servers(mcp)
    if servers:
        plugin["mcpServers"] = servers
    if variables:
        plugin["variables"] = {
            "type": "object",
            "properties": {
                name: {"type": "string", "title": name, "default": ""} for name in variables
            },
        }
    return plugin


def build_marketplace(claude_marketplace, claude_plugin):
    # Cursor's marketplace schema rejects extra entry fields (additionalProperties: false).
    # Version and keywords stay on plugin.json. Official marketplaces ship name, source, description.
    entry = next(p for p in claude_marketplace["plugins"] if p["name"] == claude_plugin["name"])
    plugin_entry = {
        "name": entry["name"],
        "source": entry["source"],
        "description": entry["description"],
    }
    return {
        "name": claude_marketplace["name"],
        "owner": claude_marketplace["owner"],
        "metadata": {"description": claude_marketplace["description"].replace("Claude Code", "Claude Code and Cursor")},
        "plugins": [plugin_entry],
    }


def split_frontmatter(text, path):
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if not match:
        sys.exit(f"error: {path} has no frontmatter")
    return match.group(1), match.group(2)


def parse_frontmatter(block):
    """Return {key: raw_lines}. Indented lines belong to the key above them."""
    fields = {}
    key = None
    for line in block.splitlines():
        top = re.match(r"^([A-Za-z][\w-]*):", line)
        if top:
            key = top.group(1)
            fields[key] = [line]
        elif key:
            fields[key].append(line)
    return fields


def scalar(lines):
    return lines[0].split(":", 1)[1].strip()


def _skill_invocation(match):
    verb = match.group("verb")
    name = match.group("name")
    args = match.group("args")
    if verb.lower().startswith("never"):
        lead = "Never follow" if verb[0].isupper() else "never follow"
        return f"{lead} the `{name}` skill"
    lead = "Read and follow" if verb[0].isupper() else "read and follow"
    if args and args != "...":
        return f"{lead} the `{name}` skill's `SKILL.md` (input: {args})"
    return f"{lead} the `{name}` skill's `SKILL.md`"


def _require_replace(text, old, new, path):
    if old not in text:
        sys.exit(f"error: {path} is missing the Claude phrase the Cursor adapter rewrites:\n{old}")
    return text.replace(old, new, 1)


def adapt_product_designer(body, path):
    """A Cursor subagent cannot hold the live interview this agent exists to run."""
    body = _require_replace(
        body,
        "Your job: interview them until the problem, the flow, and the persona are actually clear, before anyone designs a solution or an API surface.",
        "Your job: synthesize persona, flow, and problem statement from answers the parent already collected. You cannot interview the user from this subagent.",
        path,
    )
    body = _require_replace(
        body,
        "- Interviewing the user via `interview` to extract problem context, current/desired flows, and who the persona actually is.",
        "- Synthesizing problem context, current/desired flows, and persona from answers already in the prompt. The parent runs `interview` in the main thread.",
        path,
    )
    body = _require_replace(
        body,
        "1. **Interview first.** Call `Skill(skill: \"interview\", ...)` to run the actual interview: "
        "what problem, whose workflow, what's broken today, what \"done\" looks like, who/what calls this "
        "(a person, another service, a script). Let it run its rounds — don't shortcut to synthesis "
        "before the frontier of open decisions is empty.",
        "1. **Do not interview from here.** This subagent cannot question the user. If the prompt has no "
        "settled answers, stop and tell the parent to run the `interview` skill in the main thread and "
        "write the Discovery handoff there (persona, flow, problem statement, open assumptions). If the "
        "prompt already contains the user's answers, synthesize those answers into the output below. "
        "Do not ask anything new.",
        path,
    )
    return body


def adapt_agent_body(body, path):
    """Rewrite Claude Code skill calls in the generated agent. The source file stays unchanged."""
    if path.name == "product-designer.md":
        body = adapt_product_designer(body, path)
    body = SKILL_INVOCATION.sub(_skill_invocation, body)
    body = body.replace(
        "Call it with the `Skill` tool.",
        "Read and follow that skill's `SKILL.md` by its `name`.",
    )
    body = body.replace(
        "call that skill with the `Skill` tool",
        "read and follow that skill's `SKILL.md`",
    )
    body = body.replace(CLAUDE_SKILL_PREFIX, "")
    body = body.replace("calling it back would loop", "following it back would loop")
    if SKILL_CALL.search(body):
        sys.exit(f"error: {path.name} still tells Cursor to call the Skill tool after adaptation")
    return body


def build_agent(path):
    frontmatter, body = split_frontmatter(path.read_text(), path)
    fields = parse_frontmatter(frontmatter)

    lines = list(fields["name"]) if "name" in fields else [f"name: {path.stem}"]
    description = list(fields.get("description", []))
    if path.stem == "product-designer" and description:
        description.insert(
            1,
            "  In Cursor this subagent cannot interview the user. Run the `interview` "
            "skill in the main thread instead of delegating a live interview here.",
        )
    lines += description

    model = scalar(fields["model"]) if "model" in fields else None
    lines.append(f"model: {MODEL_MAP.get(model, DEFAULT_MODEL)}")

    if "tools" in fields:
        tools = set(json.loads(scalar(fields["tools"])))
        if not tools & WRITE_TOOLS:
            lines.append("readonly: true")

    notice = f"<!-- Generated by scripts/sync_cursor.py from agents/{path.name}. Do not edit. -->\n"
    body = adapt_agent_body(body, path)
    return "---\n" + "\n".join(lines) + "\n---\n" + notice + body


def expected_files():
    claude_plugin = load_json(CLAUDE_DIR / "plugin.json")
    claude_marketplace = load_json(CLAUDE_DIR / "marketplace.json")
    mcp_path = ROOT / ".mcp.json"
    mcp = load_json(mcp_path) if mcp_path.is_file() else {}

    files = {
        CURSOR_DIR / "plugin.json": dump_json(build_plugin(claude_plugin, mcp)),
        CURSOR_DIR / "marketplace.json": dump_json(build_marketplace(claude_marketplace, claude_plugin)),
    }
    for agent in sorted(AGENTS_DIR.glob("*.md")):
        files[CURSOR_AGENTS_DIR / agent.name] = build_agent(agent)
    return files


def main():
    check = "--check" in sys.argv[1:]
    files = expected_files()
    stale_agents = set(CURSOR_AGENTS_DIR.glob("*.md")) - set(files) if CURSOR_AGENTS_DIR.is_dir() else set()

    if check:
        stale = [p for p, content in files.items() if not p.is_file() or p.read_text() != content]
        stale += sorted(stale_agents)
        for path in stale:
            print(f"stale: {path.relative_to(ROOT)}")
        if stale:
            print("Run: python3 scripts/sync_cursor.py")
            return 1
        print("Cursor plugin files are up to date.")
        return 0

    CURSOR_AGENTS_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in files.items():
        path.write_text(content)
        print(f"wrote: {path.relative_to(ROOT)}")
    for path in stale_agents:
        path.unlink()
        print(f"removed: {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
