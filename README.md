# LLM API Scope (apiscope)

a tool for LLM agents to read and cache structured documents from remote.

## install

use [pipx](https://github.com/pypa/pipx) for isolated installation:

```bash
pipx install llm-api-scope
```

## how it works

apiscope fetches specifications from local files or remote URLs, caches them, and outputs structured JSON that agents can consume directly. no html parsing, no keyword ranking — just faithful extraction from the source document.

## commands

run `apiscope --help` to see all available commands.

### openapi

browse OpenAPI specifications with subcommands for discovering, listing, and describing operations.

aliases let you register frequently used specs once and reference them by short name. fetching is transparent — local copies are cached for fast repeat access, and a proxy can be configured for restricted networks.

## future

- read RFC documents by number
- read academic papers from arxiv
- more formal document formats as the need arises

## license

MIT
