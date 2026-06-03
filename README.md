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

### rfc

read, search, and navigate RFC documents from the IETF.

the metadata index is mirrored once via rsync. individual text files are fetched on demand and cached locally. you can browse the table of contents, jump to a section (XML) or page (TXT), filter the index by status or source, and run keyword searches against fulltext content.

### repo

sync documentation directories from any git repository to a local cache.

register repositories by URL with a target subdirectory and a ref — a branch, tag, or commit. the sync command clones with shallow depth, blobless filter, and sparse checkout so only the needed tree and files come over the wire. extracted docs land in the cache under a stable hash path, and a configurable TTL avoids redundant re-fetches. provider-agnostic, zero auth.

## future

- read academic papers from arxiv
- more formal document formats as the need arises

## license

MIT
