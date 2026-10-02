# LLM API Scope (apiscope)

a tool for LLM agents to read and cache structured documents from remote.

## install

use [pipx](https://github.com/pypa/pipx) for isolated installation:

```bash
pipx install llm-api-scope
```

## how it works

apiscope has two ideas: a registered source, and a tree you navigate by address.
text is the default output; `--json` prints the data layer instead.

### manage

`apiscope add` registers a source with a name, a location, and a type.
`apiscope remove` deletes it.
`apiscope list` shows what is registered, filtered by type.

five document types share one command surface:

- `filesystem` reads a local file or directory
- `repo` reads a directory inside a [git](https://git-scm.com) repository
- `openapi` reads an [OpenAPI](https://www.openapis.org) specification
- `rfc` reads an [IETF](https://www.ietf.org) document
- `llmstxt` reads a [site index](https://llmstxt.org) that lists documentation pages

```bash
apiscope add docs https://example.test/docs/llms.txt --type llmstxt
apiscope add api https://github.com/example/api.git/docs@main --type repo
apiscope list all
```

### use

`apiscope sync` fetches sources into a local cache.
`apiscope view` shows the cached structure, and `apiscope read` reads one node.

view and read share the same address: a source name plus an optional route.

```bash
apiscope sync all
apiscope view docs
apiscope read docs 1.2
```

every source projects into one tree.
an ordinary node has children; a leaf has none.
a view line is `- [index] key: description`, where the index is a tree address.
an index from view always works with read.

### skill

`apiscope skill` prints or installs a combined command reference and strategy guide for AI agents.
run `apiscope skill show` to print it, or `apiscope skill install` to install it under `~/.agents/skills/apiscope`.

agents read this once at onboarding instead of running `--help` repeatedly.

### configuration

apiscope reads three configuration layers in order.
the global file is `~/.apiscope/config.json`.
the project file is `.apiscope/config.json`, and the local file is `.apiscope/local.json`.
`--global` uses the global layer only and skips project discovery.

the public setting holds the default source ttl in days.
the local setting holds the proxy.

```json
{
  "setting": {
    "public": {"doc_ttl": 7},
    "local": {"proxy": "http://proxy.example.test:8080"}
  }
}
```

the cache lives in the app directory of the selected layer, and the rest of its rules sit under `## commands`.

## commands

### add

register a source:

```bash
apiscope add <name> <source> --type <type> [--ttl <days>]
```

### remove

delete a source:

```bash
apiscope remove <name>
```

### list

list registered sources:

```bash
apiscope list <selector> [--limit <n>] [--offset <n>]
```

the selector is one of all, filesystem, repo, openapi, rfc, or llmstxt.

### sync

fetch sources into the cache:

```bash
apiscope sync <selector> [<name>] [--force]
```

the selector is the same as in list, and the optional name narrows the range to one source.
a source refreshes when its cache is older than its ttl, and `--force` ignores the ttl.
`repo` clones with shallow depth, and a subpath selects files with a sparse checkout.
`llmstxt` reads the index page, downloads the pages it lists, and skips a failed page.

### view

show the cached structure of an address:

```bash
apiscope view <address> [--depth <n>]
```

depth caps the levels below the scope; the default is unlimited.

### read

read one node:

```bash
apiscope read <address> [<index>]
```

the index is optional when the address already points at a leaf.

### skill

print or install the agent skill:

```bash
apiscope skill show
apiscope skill install [<target>]
```

install defaults to `~/.agents/skills/apiscope`.

## future

- read academic papers from arxiv
- more formal document formats as the need arises

## license

MIT
