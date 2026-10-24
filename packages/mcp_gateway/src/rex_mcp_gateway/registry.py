"""Which MCP servers exist, how to reach them, and the permission tier of every tool."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

import yaml

Tier = Literal["R", "W", "A"]
_ENV = re.compile(r"\$\{([A-Z0-9_]+)\}")


@dataclass(frozen=True)
class ToolPolicy:
    tier: Tier = "A"
    timeout_s: float = 20.0
    undo: str | None = None  # name of the compensating tool on the same server


@dataclass
class ServerSpec:
    name: str
    command: list[str] | None = None  # stdio
    url: str | None = None  # streamable HTTP
    inprocess: Any = None  # an MCPServer instance (tests / built-ins)
    env: dict[str, str] = field(default_factory=dict)
    default_tier: Tier = "A"
    tools: dict[str, ToolPolicy] = field(default_factory=dict)

    def policy(self, tool: str) -> ToolPolicy:
        return self.tools.get(tool, ToolPolicy(tier=self.default_tier))


@dataclass
class Registry:
    servers: dict[str, ServerSpec]
    allowlists: dict[str, set[str]] = field(default_factory=dict)

    def tier_for(self, server: str, tool: str) -> Tier:
        """Declared tier for the tool, else the server default (which itself defaults to the strictest, A)."""
        return self.servers[server].policy(tool).tier

    def allowed(self, specialist: str, server: str) -> bool:
        return server in self.allowlists.get(specialist, set())


def _expand(value: Any, env: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        return _ENV.sub(lambda m: env.get(m.group(1), ""), value)
    if isinstance(value, list):
        return [_expand(v, env) for v in value]
    if isinstance(value, dict):
        return {k: _expand(v, env) for k, v in value.items()}
    return value


def load_registry(path: str | Path, env: Mapping[str, str] | None = None) -> Registry:
    env = os.environ if env is None else env
    raw = _expand(yaml.safe_load(Path(path).read_text()) or {}, env)
    servers: dict[str, ServerSpec] = {}
    for name, cfg in (raw.get("servers") or {}).items():
        if cfg.get("enabled", True) is False:
            continue
        tools = {t: ToolPolicy(**(p or {})) for t, p in (cfg.get("tools") or {}).items()}
        servers[name] = ServerSpec(
            name=name,
            command=cfg.get("command"),
            url=cfg.get("url"),
            env=cfg.get("env") or {},
            default_tier=cfg.get("default_tier", "A"),
            tools=tools,
        )
    allow = {k: set(v or []) for k, v in (raw.get("allowlists") or {}).items()}
    return Registry(servers=servers, allowlists=allow)
