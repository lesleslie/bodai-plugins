# Bodai Plugins — Port Map

Authoritative port assignments for the Bodai ecosystem. Covers core Bodai components (orchestrator, memory, intelligence, quality, state) and the WWW MCP server fleet. Excludes `fastblocks` and `splashstand` per the documented scope of `bodai-plugins`.

This map is the canonical reference for plugin install commands and runtime health probes. Where it disagrees with a per-component `settings/<name>.yaml` or `pyproject.toml`, **update this map** — it's easier to grep one file than fifteen.

## Port allocation overview

| Range | Purpose |
|---|---|
| 3032–3052 | WWW MCP server HTTP transport |
| 8471 | Bifrost LLM gateway |
| 8675 | Prefect API server |
| 8676 | Crackerjack |
| 8678 | Session-Buddy |
| 8680 | Mahavishnu |
| 8682 | Akosha |
| 8683 | Dhara |
| 8686 | Crackerjack test WebSocket |
| 8690 | Mahavishnu WebSocket |
| 8691 | Mahavishnu pool WebSocket |
| 8692 | Akosha pattern WebSocket |
| 8693 | Bodai Crow (browser/automation MCP bridge) |
| 8699 | `web_reader` MCP server |
| 8765 | Session-Buddy WebSocket |

## Core Bodai components

The orchestrator ecosystem. The five with **✓ Plugin** are also registered in `.claude-plugin/marketplace.json`; the rest are infrastructure listeners that the orchestrator depends on.

| Component | Default Port | Plugin | Role |
|---|---|---|---|
| Bifrost | 8471 | — | LLM gateway (OpenAI-compatible proxy) |
| Prefect API | 8675 | — | Workflow orchestration backend (`uvicorn prefect.server.api.server`) |
| Crackerjack | 8676 | ✓ Plugin | Quality & CI inspection |
| Session-Buddy | 8678 | ✓ Plugin | Memory & reflection MCP server |
| Mahavishnu | 8680 | ✓ Plugin | Orchestrator |
| Akosha | 8682 | ✓ Plugin | Cross-system intelligence (seer) |
| Dhara | 8683 | ✓ Plugin | Persistent state curator |
| Crackerjack test WS | 8686 | — | Crackerjack test execution WebSocket |
| Mahavishnu WS | 8690 | — | Real-time workflow events |
| Mahavishnu pool WS | 8691 | — | Pool status events |
| Akosha pattern WS | 8692 | — | Pattern detection events |
| Bodai Crow | 8693 | — | Browser/automation MCP bridge |
| web_reader | 8699 | — | Webpage ingestion MCP server |
| Session-Buddy WS | 8765 | — | Real-time metrics WebSocket |

## WWW MCP servers

See `www-mcp-servers/PORTMAP.md` for the full table with source-of-truth column. Summary, sorted by port:

| Server | Default Port | Role |
|---|---|---|
| excalidraw-mcp | 3032 | Diagramming |
| raindropio-mcp | 3034 | Bookmarks |
| opera-cloud-mcp | 3037 | Hospitality PMS |
| unifi-mcp | 3038 | Network operations |
| mailgun-mcp | 3039 | Email operations |
| graphics-mcp | 3040 | Image operations |
| porkbun-dns-mcp | 3042 | DNS management |
| porkbun-domain-mcp | 3043 | Domain lifecycle |
| neo4j-mcp | 3045 | Graph database |
| synxis-crs-mcp | 3046 | Reservations |
| synxis-pms-mcp | 3047 | Property operations |
| langsmith-mcp | 3048 | Observability |
| css-mcp | 3050 | CSS analysis |
| penpot-api-mcp | 3051 | Design automation |
| spline-mcp | 3052 | 3D scenes |

All 15 are registered as plugins in `.claude-plugin/marketplace.json`.

## Excluded from this map

- **`fastblocks`** — web framework; not a Bodai plugin or MCP server. Lives in its own repo with its own port allocations.
- **`splashstand`** — web app; same reasoning as fastblocks.

If `fastblocks` or `splashstand` ports collide with the ranges above, the collision is incidental — neither component participates in the Bodai runtime.

## Port allocation policy for new components

- **WWW MCP servers**: next free slot above 3052 (i.e. start at 3053).
- **Core Bodai components**: prefer the 86xx range (Bifrost's 8471 and web_reader's 8699 are the exceptions). Each new core component should pick a free 86xx port.
- **Secondary listeners** (WebSocket, canvas servers, etc.): document in the same row as the primary port, in a "Secondary ports" section.

## Audit procedure

To verify the WWW MCP server block matches `www-mcp-servers/PORTMAP.md`:

```bash
# Pull the table from the source of truth and diff against this file.
diff \
  <(awk '/^\| \[[a-z]/' /Users/les/Projects/www-mcp-servers/PORTMAP.md | sort) \
  <(awk '/^\| \[[a-z]/' /Users/les/Projects/bodai-plugins/PORTMAP.md | sort)
```

Empty diff = consistent.

To detect new -mcp servers that aren't yet in this map:

```bash
ls -d /Users/les/Projects/*-mcp | xargs -I{} basename {}
```

Compare against the WWW MCP servers table.
