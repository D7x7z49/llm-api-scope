# CHANGELOG

<!-- version list -->

## v0.7.0 (2026-06-04)

### Features

- **openapi**: Add --limit and --offset pagination to list
  ([`a1b4259`](https://github.com/D7x7z49/llm-api-scope/commit/a1b4259988c0151a6292002a8ad5ee92bb4606c2))

- **skill**: Add skill subcommand with command reference and strategy guide
  ([`5ac913e`](https://github.com/D7x7z49/llm-api-scope/commit/5ac913eb6bbd718020cbe4ac9a89bdcf0aa89889))


## v0.6.1 (2026-06-03)

### Bug Fixes

- **config**: Auto-create empty project config on first run
  ([`374920e`](https://github.com/D7x7z49/llm-api-scope/commit/374920e209b81db4f6ebb629a11531f9a4136d86))


## v0.6.0 (2026-06-03)

### Continuous Integration

- Enable pdm package cache in CI workflow
  ([`718e50c`](https://github.com/D7x7z49/llm-api-scope/commit/718e50cb47efe9e8ab1abf6897b2c985c7598553))

- Fix mypy missing target paths in CI workflow
  ([`ea0cf09`](https://github.com/D7x7z49/llm-api-scope/commit/ea0cf094cb376d84ee383bf9e87098d9e236d67b))

### Documentation

- **repo**: Add repo section to README and usage
  ([`c56ac33`](https://github.com/D7x7z49/llm-api-scope/commit/c56ac332e35b60f12100bbcc97794d2e7357cafc))

### Features

- **repo**: Add repo subcommand skeleton with basic config structure
  ([`c9aad18`](https://github.com/D7x7z49/llm-api-scope/commit/c9aad180300090aada4b3c91ce178340149c0fca))

- **repo**: Implement add, remove, and list commands
  ([`c666c9f`](https://github.com/D7x7z49/llm-api-scope/commit/c666c9f443329c217b14356bc1626e926ee09f34))

- **repo**: Implement sync with minimal git clone pipeline
  ([`381973e`](https://github.com/D7x7z49/llm-api-scope/commit/381973eea402ddf6f72a4010adefde814a8c14a8))

### Performance Improvements

- **repo**: Truncate sha256_id to 8 chars, clarify sync comments
  ([`e5c110a`](https://github.com/D7x7z49/llm-api-scope/commit/e5c110ab61c847a1ed521a20b9ab56c26cc273fb))


## v0.5.1 (2026-06-03)

### Continuous Integration

- Rewrite CI workflows
  ([`2232b51`](https://github.com/D7x7z49/llm-api-scope/commit/2232b5177184bd54fbf7e15b43074071a549bb66))

### Documentation

- Add rfc command section to README
  ([`efb340a`](https://github.com/D7x7z49/llm-api-scope/commit/efb340a482f294bb2b8a4cf7575c3a5fcc9ef302))

### Performance Improvements

- **cache**: Add TTL-based cache invalidation with --force override
  ([`10aeacd`](https://github.com/D7x7z49/llm-api-scope/commit/10aeacd7d0a65234da8c93e480f733e35c377bc1))


## v0.5.0 (2026-06-03)

### Chores

- Remove accidentally tracked tmp/repo/pdm CI files
  ([`97253c8`](https://github.com/D7x7z49/llm-api-scope/commit/97253c85b2715f4b135873c7aa7e13d5570a8cb1))

### Documentation

- Add CLI usage reference with EBNF format
  ([`1650034`](https://github.com/D7x7z49/llm-api-scope/commit/165003411b0c6623f7fbb1a53302104130d754e5))

### Features

- **rfc**: Add rfc command group with sync, info, read, and search
  ([`2494d2b`](https://github.com/D7x7z49/llm-api-scope/commit/2494d2b8f56d9601684e4ec6978d3789ba993ce7))

- **rfc**: Add sync and info subcommands with metadata display
  ([`1dba08b`](https://github.com/D7x7z49/llm-api-scope/commit/1dba08bdbf71fac756e436516414621b25d41dfd))

- **rfc**: Register rfc command group and enhance health check
  ([`07fb0d5`](https://github.com/D7x7z49/llm-api-scope/commit/07fb0d50ad3bd1a584b4080c768e5134fc4ab50f))


## v0.4.0 (2026-06-01)

### Chores

- Add .pi/prompts and fix-headers pre-commit hook
  ([`b5adb5d`](https://github.com/D7x7z49/llm-api-scope/commit/b5adb5d851982666b4e53e795f2fd2e0ebe74413))

- Sync .pi prompts and add experience file support
  ([`53a3740`](https://github.com/D7x7z49/llm-api-scope/commit/53a3740955e641bb03c8ac4100e9d531315c3167))

- **scripts**: Add subcommand directory generator
  ([`9d10415`](https://github.com/D7x7z49/llm-api-scope/commit/9d104150ab4a8dd51ac96a522bbb7c92fa5f597d))

### Code Style

- Add file header comments via fix-headers hook
  ([`eba817b`](https://github.com/D7x7z49/llm-api-scope/commit/eba817b7daad5c6369ad1ab9d5a3df16be44ff61))

- Add file header comments via fix-headers hook
  ([`b9022e8`](https://github.com/D7x7z49/llm-api-scope/commit/b9022e8217597572a8df63f50d30ca48552422e6))

### Continuous Integration

- Add local pr creation script
  ([`4cb3315`](https://github.com/D7x7z49/llm-api-scope/commit/4cb33151cfac69d2077548431270ee167c9bd4f7))

### Documentation

- Add writing style conventions and rewrite loglight spec
  ([`f88a2f4`](https://github.com/D7x7z49/llm-api-scope/commit/f88a2f4704013ff539e13a52ad719eb0e9c1648c))

- Refresh README, AGENTS, and CONTRIBUTING for rewrite branch
  ([`03a8e7b`](https://github.com/D7x7z49/llm-api-scope/commit/03a8e7b4fc0c1a1ecd85188e0f53037fa6ebb411))

### Features

- **openapi**: Add doc command group for alias management
  ([`0c3c6a8`](https://github.com/D7x7z49/llm-api-scope/commit/0c3c6a8922840131be2ebdf779cc5bc48f8fea81))

- **openapi**: Add OpenapiReader with load, filter, lookup, and ref resolution
  ([`39abc6a`](https://github.com/D7x7z49/llm-api-scope/commit/39abc6af1c0c5d216b4a37c7f15a7be5b96b1b23))

- **openapi**: Add proxy support for remote spec fetching
  ([`4c4022c`](https://github.com/D7x7z49/llm-api-scope/commit/4c4022ca160c51433e39ee0b474551393ac84c03))

- **openapi**: Add spec fetching with local copy and remote download
  ([`7371f3e`](https://github.com/D7x7z49/llm-api-scope/commit/7371f3e0c45663b2c8481dd6ac81ba2ba1a1e03e))

- **openapi**: Implement operation commands with info, list, and describe
  ([`21bc55b`](https://github.com/D7x7z49/llm-api-scope/commit/21bc55bcdfe6822030386c5af933670e46c7c114))

### Refactoring

- Apply lowercase style, remove docstrings, add help to all commands
  ([`9a52d67`](https://github.com/D7x7z49/llm-api-scope/commit/9a52d679b586cf706407fc45752934d541a1c857))

- Refresh project foundation with pydantic config and typer CLI
  ([`1d251e6`](https://github.com/D7x7z49/llm-api-scope/commit/1d251e60a99b88295bfcf0267645b58fcdc34b65))

- Rename pr target file from pr.md to pr.tmp
  ([`f3d2175`](https://github.com/D7x7z49/llm-api-scope/commit/f3d2175ca9dda4be60d389aae01618c1a1eac674))

- Strip old CLI and note system, add quality tooling
  ([`188bbd7`](https://github.com/D7x7z49/llm-api-scope/commit/188bbd7b8f9875d0c144bf103220119278fab8d0))

- **openapi**: Rename doc subcommand to spec
  ([`19ee224`](https://github.com/D7x7z49/llm-api-scope/commit/19ee22499d52d2433d225329a1ddbf5b5df29003))


## v0.3.1 (2026-03-01)

### Bug Fixes

- **note**: Remove interactive prompt in second phase of note creation
  ([`3ad27b7`](https://github.com/D7x7z49/llm-api-scope/commit/3ad27b735943474e8014005bc4e0fc6bd8320a24))


## v0.3.0 (2026-03-01)

### Features

- **core**: Implement temporal clustering, pattern matching, and note system core
  ([`107657f`](https://github.com/D7x7z49/llm-api-scope/commit/107657f36411df6b1f8d29966a3bab9b291cdcbd))

- **note**: Integrate note command with improved module structure
  ([`e47ea95`](https://github.com/D7x7z49/llm-api-scope/commit/e47ea95e40e5d5eeeae985d95d06edfd032e8d5a))


## v0.2.1 (2026-02-06)

### Bug Fixes

- Update project metadata and improve package description
  ([`cac2bcb`](https://github.com/D7x7z49/llm-api-scope/commit/cac2bcb77a6e32da1e190ffcd6585e762ef6f70e))


## v0.2.0 (2026-01-21)

### Bug Fixes

- Correct semantic-release config and add workflow headers
  ([`9eb3750`](https://github.com/D7x7z49/llm-api-scope/commit/9eb375051234b912dbf240426530662aa45157d5))

- Update semantic-release config to version pyproject.toml
  ([`c0d2d70`](https://github.com/D7x7z49/llm-api-scope/commit/c0d2d7017b79609de5ec7bac02df74035c1b1f94))

### Continuous Integration

- Add automated PyPI publishing workflow
  ([`44a26f4`](https://github.com/D7x7z49/llm-api-scope/commit/44a26f4fbc9ab9af38dd8a31119f66591b9f2aec))

- Add commitlint for PR validation
  ([`a67ab7f`](https://github.com/D7x7z49/llm-api-scope/commit/a67ab7f10f3d7052bb9bad41ad656dbda4560c64))

- Fix semantic-release config compatibility
  ([`c0759e5`](https://github.com/D7x7z49/llm-api-scope/commit/c0759e5542053d15893d3b6de3341d8dd25ff523))

- Setup continuous integration and automated releases
  ([`b9214ff`](https://github.com/D7x7z49/llm-api-scope/commit/b9214ff2efd9f4e3f6d3b14536fb7e64a3aab750))

- **semantic-release**: Migrate config from releaserc.json to pyproject.toml
  ([`ce9c9a7`](https://github.com/D7x7z49/llm-api-scope/commit/ce9c9a7e71ce7de21c940cf3d83f8d690edfebf1))

- **workflows**: Fix publish workflow and remove unused build config
  ([`a64c06c`](https://github.com/D7x7z49/llm-api-scope/commit/a64c06cebe72f0ee92768d414bd8bae1a9692543))

### Documentation

- Add contribution guidelines
  ([`fb8593d`](https://github.com/D7x7z49/llm-api-scope/commit/fb8593de92c22e2249a0eeebea370fc33a18bdf3))

### Features

- Add code quality and formatting tools
  ([`1c112f0`](https://github.com/D7x7z49/llm-api-scope/commit/1c112f0269a5b32a3c2fd01fe3e29c44543af71a))

- Add development dependencies and tooling
  ([`fce49b8`](https://github.com/D7x7z49/llm-api-scope/commit/fce49b8afdb65b1a7f6e1c730ca0f15bdc92cf68))

### Refactoring

- Remove unused hishel dependency
  ([`4ad65bd`](https://github.com/D7x7z49/llm-api-scope/commit/4ad65bd28c53a28fcdd7a8a7fd2f12540c8fafb5))


## v0.1.2 (2026-01-19)

- Initial Release
