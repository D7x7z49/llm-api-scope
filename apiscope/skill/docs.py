# apiscope/skill/docs.py

STRATEGY_GUIDE = """\
PREMISE

  apiscope is a content acquisition layer, not a consumption layer.
  it fetches high-quality reference materials to local cache, then
  you use your preferred tools (ripgrep, grep, less) to consume them.

  - openapi: structured api specifications with built-in analysis helpers
  - rfc: internet standards and best current practice documents
  - repo: git repository documentation for offline access

CLASSIFICATION

  management commands (run once, configure the tool)

    - apiscope health
    - apiscope openapi spec add / remove / list
    - apiscope repo add / remove / list / sync
    - apiscope rfc sync

  usage commands (run repeatedly, query content)

    - apiscope openapi info / list / describe
    - apiscope rfc info / read / search

PREREQUISITES

  the grammar notation used in this section follows <RFC 5234> ABNF.
  the key words "MUST", "SHOULD", and "MAY" are to be interpreted
  as described in <RFC 2119>.

  openapi-query
    =  spec-add *(info / list / describe)
    ; spec-add MUST precede any query command

  rfc-local
    =  sync read
    ; sync SHOULD precede read for local access

  rfc-local-info
    =  sync info
    ; sync SHOULD precede info for metadata lookup

  repo-consume
    =  add sync grep
    ; add then sync MUST precede local consumption

WORKFLOWS

  explore-api
    =  spec-add info list describe
    ; 1. register the spec
    ; 2. check metadata
    ; 3. browse operations
    ; 4. examine a specific operation

  read-rfc
    =  sync *search read
    ; 1. sync index
    ; 2. optionally search for relevant RFCs
    ; 3. read the selected RFC

  integrate-repo
    =  add sync grep
    ; 1. register the repository
    ; 2. sync all repos
    ; 3. use ripgrep or grep on local cache

TIPS

  cache strategy

    each domain has a different cache ttl reflecting content
    stability. the [--force] flag MUST only be used when you
    expect the remote content has changed since last fetch.

    - openapi: 1 day
    - rfc: 30 days
    - repo: 7 days

  config hierarchy

    global config (<~/.apiscope/config.json>) holds personal
    defaults. project config (<.apiscope.config.json>) holds
    team-specific entries. project values override global ones
    where overlap is defined.

    [openapi spec add] without [-g] writes to project config.
    teammates who clone the project get the same aliases.

  openapi alias naming

    aliases are shortcuts for spec URLs. use a naming convention
    that makes the source obvious without checking [spec list].

    - github-api, petstore-v3, stripe-v1

  acquisition before analysis

    rfc and repo pull documents to local cache. do not treat
    apiscope search as a replacement for grep or ripgrep. the
    intended workflow is: acquire local copy, then analyze with
    your preferred tools.

    openapi is the exception. it provides [list] for breadth,
    [describe] for depth, and [info] for metadata. use [list]
    first to scan endpoints, then [describe] to extract a
    specific operation in detail.
"""
