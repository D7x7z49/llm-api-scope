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

a source link is registered once; a repeated link fails, even under another name or type.
a private source in the home configuration uses an absolute path, and a project source uses a path relative to the project root.

six document types share one command surface:

- `filesystem` reads a local file or directory
- `repo` reads a directory inside a [git](https://git-scm.com) repository
- `openapi` reads an [OpenAPI](https://www.openapis.org) specification
- `rfc` reads an [IETF](https://www.ietf.org) document
- `llmstxt` reads a [site index](https://llmstxt.org) that lists documentation pages
- `arxiv` reads one arXiv paper by its canonical identifier

```bash
apiscope add docs https://example.test/docs/llms.txt --type llmstxt
apiscope add api https://github.com/example/api.git/docs@main --type repo
apiscope add paper 1706.03762 --type arxiv
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
the local setting holds the proxy and the `no_proxy` bypass list.

```json
{
  "setting": {
    "public": {"doc_ttl": 7},
    "local": {
      "proxy": "http://proxy.example.test:8080",
      "no_proxy": "internal.example.test,localhost"
    }
  }
}
```

the HTTP client uses only the configured `[proxy]` and `[no_proxy]` and ignores environment proxy variables.
for repository operations, apiscope passes configured proxy settings to `git` and `gh`; when `[proxy]` is unset, it does not set or clear their proxy.
`[no_proxy]` is a comma-separated list of hosts, domains, or `*` that bypasses the configured proxy.

the cache lives in the app directory of the selected layer, and the rest of its rules sit under `## commands`.

## commands

### add

register a source:

```bash
apiscope add <name> <source> --type <type> [--ttl <days>]
```

`arxiv` accepts a canonical identifier such as `1706.03762` or `hep-th/9901001`; append `vN` for a fixed version. URL forms are not accepted.

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

the selector is one of all, filesystem, repo, openapi, rfc, llmstxt, or arxiv.

### sync

fetch sources into the cache:

```bash
apiscope sync <selector> [<name>] [--force]
```

the selector is the same as in list, and the optional name narrows the range to one source.
a source refreshes when its cache is older than its ttl, and `--force` ignores the ttl.
`repo` clones with shallow depth, and a subpath selects files with a sparse checkout.
`llmstxt` reads the index page, prefers the markdown version of each page, and skips a failed page.
`arxiv` prefers structured HTML, falls back to TeX source, and does not parse PDF-, PostScript-, or DVI-only submissions.

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

### bookmark

save a named reference and reopen it later:

```bash
apiscope bookmark add <id> <mode> <target>... --description <text>
apiscope bookmark list [<group>]
apiscope bookmark use <id>
apiscope bookmark remove <id>
apiscope bookmark prune [--invalid]
```

mode is file, view, read, or group; a group takes five to nine member ids.
bookmarks live in a global file and a project file, and the project wins.

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
