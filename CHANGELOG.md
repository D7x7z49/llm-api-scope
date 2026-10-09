# CHANGELOG

<!-- version list -->

## v0.12.2 (2026-10-09)

### Bug Fixes

- **llmstxt**: Cache a page that is also a parent
  ([`16a2588`](https://github.com/D7x7z49/llm-api-scope/commit/16a25883d85b8a6f3a58e1aad685764a58ce9d49))

### Documentation

- **branch**: Allow a number as a later name word
  ([`2424508`](https://github.com/D7x7z49/llm-api-scope/commit/24245086d8ebb5c382256158edd417ed632a1df7))

### Performance Improvements

- **cache**: Shorten a cache name to a digest prefix
  ([`6486d77`](https://github.com/D7x7z49/llm-api-scope/commit/6486d7795aebe32c35996208972a0e58007e5cab))


## v0.12.1 (2026-10-08)

### Bug Fixes

- **bookmark**: Map the target reason to each boundary code
  ([`2a5e0f6`](https://github.com/D7x7z49/llm-api-scope/commit/2a5e0f6f9622173854283ca9bfd6cbed0f9d4e6a))

- **bookmark**: Reject a read target that bookmark use cannot project
  ([`6e50eda`](https://github.com/D7x7z49/llm-api-scope/commit/6e50eda5c4df2531be9931fde35a7996646928e7))

- **validation**: Name the field, rule, and value on invalid options
  ([`2bb9aea`](https://github.com/D7x7z49/llm-api-scope/commit/2bb9aeab6f69d7eacf00da866e238aa8b4350bb6))

### Code Style

- Drop the non command docstrings
  ([`88f3e69`](https://github.com/D7x7z49/llm-api-scope/commit/88f3e69b2efcf4caaa80c031aab5f83ccc1d33ca))

### Refactoring

- **bookmark**: Drop unused resolver state
  ([`3f91506`](https://github.com/D7x7z49/llm-api-scope/commit/3f91506e33338c29aeb6243663de817d80fb89de))

### Testing

- Divide the library tests by type and lift data into fixtures
  ([`f6db740`](https://github.com/D7x7z49/llm-api-scope/commit/f6db74063cb58410e3113f6f3f236f34715dd410))

- Make the home rule true and align the test tree
  ([`af9640a`](https://github.com/D7x7z49/llm-api-scope/commit/af9640a18ba0d280b14101e68bf182dd1ad1a2bf))

- Unblock the lock test and reuse the transport fake
  ([`fd26ff4`](https://github.com/D7x7z49/llm-api-scope/commit/fd26ff4d5305abbccb420e611709676debb9337e))

- **coverage**: Report branch coverage for the fast suite
  ([`0558b92`](https://github.com/D7x7z49/llm-api-scope/commit/0558b92dabcce6f43fbc82416b83c9c66fffc850))

- **e2e**: Add an installed console script scope
  ([`60f222f`](https://github.com/D7x7z49/llm-api-scope/commit/60f222fd3f62515824fc78a9ea9fe652b6a60043))

- **tests**: Constrain the tree shape and lift data into fixtures
  ([`6259186`](https://github.com/D7x7z49/llm-api-scope/commit/625918684c3a8074d5744a7236f7f04b8d0df67b))

- **validation**: Cover the finding branches
  ([`4cf5b04`](https://github.com/D7x7z49/llm-api-scope/commit/4cf5b04290fed3dfa7f394a866b116d1d2a4ae1d))

- **validation**: Table the describe finding cases
  ([`ed8f5f0`](https://github.com/D7x7z49/llm-api-scope/commit/ed8f5f026fb5a54b74f3371e2c7b2fa25a217daa))


## v0.12.0 (2026-10-08)

### Build System

- **deps**: Drop the unused python-dotenv
  ([`8a28b34`](https://github.com/D7x7z49/llm-api-scope/commit/8a28b3400f92b786ca31cbe3017ebc7374c575c9))

- **deps**: Switch the http client to httpx2
  ([`04739f3`](https://github.com/D7x7z49/llm-api-scope/commit/04739f3bff85c88b18b10e7d00a25174d8ac1db9))

### Chores

- **packaging**: Declare the supported python versions
  ([`7e556a2`](https://github.com/D7x7z49/llm-api-scope/commit/7e556a2af8aa1443a94462184ec160993ea93785))

### Continuous Integration

- Check the apiscope scope shape
  ([`7714b28`](https://github.com/D7x7z49/llm-api-scope/commit/7714b287ce6c708e13ef635961f233639d558acb))

- Check the supported python versions
  ([`8a502c4`](https://github.com/D7x7z49/llm-api-scope/commit/8a502c417b8448f92d03c914ead3a4556620ce86))

- Release only after the ci run on main succeeds
  ([`8b5403a`](https://github.com/D7x7z49/llm-api-scope/commit/8b5403a1d04903a78be709612e0c389250a46be5))

- Test every supported python version
  ([`85d5abd`](https://github.com/D7x7z49/llm-api-scope/commit/85d5abda36882518f5a94b3c8d340d68ad642c32))

### Documentation

- **experience**: Record the function purpose guidance
  ([`a0e70e6`](https://github.com/D7x7z49/llm-api-scope/commit/a0e70e6d5149489aa101f4c2de207dbdd1019fbb))

### Features

- **arxiv**: Add arXiv paper source support
  ([`7889ed1`](https://github.com/D7x7z49/llm-api-scope/commit/7889ed11a82ff050a5026ea14c90b35e124e7fd0))

### Refactoring

- **apiscope**: Align the group scopes with the scope shape
  ([`f98967d`](https://github.com/D7x7z49/llm-api-scope/commit/f98967d4f97a86d0abb2404c4bc828d0439435ce))


## v0.11.0 (2026-10-07)

### Documentation

- **bookmark**: Document the command in the readme
  ([`640a3ae`](https://github.com/D7x7z49/llm-api-scope/commit/640a3ae6967e11bec85e6bbc5f0ba7c5232a40eb))

### Features

- **bookmark**: Save and reopen references to cached sources
  ([`107aaab`](https://github.com/D7x7z49/llm-api-scope/commit/107aaabc209e8e6fb17941bfbd7891737fc245b2))

### Refactoring

- **bookmark**: Derive the list status once
  ([`7059123`](https://github.com/D7x7z49/llm-api-scope/commit/7059123c06fede6373729e6ef7b079fafb700593))

- **bookmark**: Return the cache metadata from load_source
  ([`0516bd4`](https://github.com/D7x7z49/llm-api-scope/commit/0516bd40ec185d9cd8802aa101e3b5960bf4d6aa))

### Testing

- **bookmark**: Assert the rendered view body
  ([`5756f81`](https://github.com/D7x7z49/llm-api-scope/commit/5756f811235f9a057917b480dc2b64609fbf471e))


## v0.10.0 (2026-10-05)

### Bug Fixes

- **output**: Show raw text values and match the foot to the head
  ([`d7f2b2e`](https://github.com/D7x7z49/llm-api-scope/commit/d7f2b2e28463fef2ce286a9c604308b4512cbb06))

- **source**: Align cache identity with registered links
  ([`cfede18`](https://github.com/D7x7z49/llm-api-scope/commit/cfede1895cbdfd92f396f228d53fe1b40fd575c6))

### Chores

- **pdm**: Load the project .env on pdm run
  ([`ba0e253`](https://github.com/D7x7z49/llm-api-scope/commit/ba0e25372f0d0b2b401e8b4a31c34b11127899b6))

### Documentation

- Describe the proxy scope for the client and git
  ([`4e2de18`](https://github.com/D7x7z49/llm-api-scope/commit/4e2de18224a13f14846783b66ec74941e9a36676))

- **agents**: Define stable project operating principles
  ([`15a7e66`](https://github.com/D7x7z49/llm-api-scope/commit/15a7e663e4893a66253da0080f48da6e62222ecb))

### Features

- **cache**: Name an entry with a short source digest
  ([`d48a740`](https://github.com/D7x7z49/llm-api-scope/commit/d48a7403113d1c08e640fd6924ee8c3fb5f3872a))

- **lock**: Serialize the write commands with a home lock
  ([`885096f`](https://github.com/D7x7z49/llm-api-scope/commit/885096f398ca3629020ac7e16139f9c7e14d53f0))

- **repo**: Select a repository path and ref with a sparse checkout
  ([`0dbbb87`](https://github.com/D7x7z49/llm-api-scope/commit/0dbbb8730b99e71b6e5aefdfaa5089a0083d0211))

- **repo**: Wrap the git calls and fall back to gh on GitHub
  ([`a962a8f`](https://github.com/D7x7z49/llm-api-scope/commit/a962a8f675b9bebcee9082a426a731bce51d6a88))

- **source**: Enforce the source forms by document type
  ([`44e3c6f`](https://github.com/D7x7z49/llm-api-scope/commit/44e3c6f957d93c2a4aae8fe4c40f2f73d73d4d28))

- **sync**: Apply the configured proxy and add a bypass list
  ([`701d225`](https://github.com/D7x7z49/llm-api-scope/commit/701d2258659c22d2b92ef2e23b50b067635643cb))

- **sync**: Report an expired cache in the bulk sync head
  ([`252d5da`](https://github.com/D7x7z49/llm-api-scope/commit/252d5da12285485569537bd32572b476dec56a1b))

### Refactoring

- **apiscope**: Model parsed sources by document type
  ([`680a8c5`](https://github.com/D7x7z49/llm-api-scope/commit/680a8c5ef617fbaa8a1249b128056152cc8fd31d))

- **read**: Drop the unused proxy parameter
  ([`397c4f6`](https://github.com/D7x7z49/llm-api-scope/commit/397c4f6a9490d0b7f8c1fa07e4e8d49a595b8db7))


## v0.9.0 (2026-10-01)

### Bug Fixes

- **gitignore**: Stop forcing project config tracking
  ([`0d7b812`](https://github.com/D7x7z49/llm-api-scope/commit/0d7b81249bca5d658bf1363a2a7165cb6572ffb6))

### Chores

- Enforce strict Ruff quality policy
  ([`c5f180e`](https://github.com/D7x7z49/llm-api-scope/commit/c5f180eb4468de94e145c7a6dc8d2723521797f5))

- Remove the archived baseline
  ([`0b573de`](https://github.com/D7x7z49/llm-api-scope/commit/0b573de96e8065304d62b08657cb38be87f51629))

- Untrack temporary files
  ([`fb5e32d`](https://github.com/D7x7z49/llm-api-scope/commit/fb5e32d789952f593e173aa6c5fe78e887b4485a))

- **ci**: Check the commit messages with commitizen
  ([`a65f93c`](https://github.com/D7x7z49/llm-api-scope/commit/a65f93c12d5a83e34fd8a0c6df785e7895330157))

### Documentation

- Add design decision guidance
  ([`19d2437`](https://github.com/D7x7z49/llm-api-scope/commit/19d243747ec77fe4a1aee06f494a21d32d54a028))

- Archive the old command reference
  ([`708e51d`](https://github.com/D7x7z49/llm-api-scope/commit/708e51dce1d7e33fca07615cf83d7caba3360645))

- Clarify agent and error handling guidance
  ([`540a6cb`](https://github.com/D7x7z49/llm-api-scope/commit/540a6cb483510d030d981e9d50fc3a01a20e4633))

- Generate the usage reference from the app
  ([`0172794`](https://github.com/D7x7z49/llm-api-scope/commit/01727942b39988346027bbfbc71b7e55c15675c2))

- Refresh the readme for the new commands
  ([`43481e0`](https://github.com/D7x7z49/llm-api-scope/commit/43481e00a92636644012aa2d9199315cb94cae92))

- **apiscope**: Add scope rules and the concrete layout
  ([`0e6e60a`](https://github.com/D7x7z49/llm-api-scope/commit/0e6e60a07f19f74ee082738e8852cae50f2fadf6))

- **experience**: Record pytest expected data guidance
  ([`5f7caa8`](https://github.com/D7x7z49/llm-api-scope/commit/5f7caa848c53025b2f00c140aba6fdb05a3e42bd))

- **health**: Reserve a placeholder for the health subcommand
  ([`96384f4`](https://github.com/D7x7z49/llm-api-scope/commit/96384f4758d53e35598afa54432b18d6127a9e95))

- **prompt**: Add a CLI usage description grammar
  ([`3005067`](https://github.com/D7x7z49/llm-api-scope/commit/3005067fbddd710881fcf49a7f3ba3d07bc04b47))

### Features

- **add**: Register project and home sources
  ([`9598a1b`](https://github.com/D7x7z49/llm-api-scope/commit/9598a1b4e53dc791db153ac2a7469200e13902f4))

- **apiscope**: Add the skill command
  ([`0122063`](https://github.com/D7x7z49/llm-api-scope/commit/0122063a4392ffbd4e8546894ae8faa7cda9d9c5))

- **apiscope**: Cache llmstxt pages and hash the content
  ([`0123079`](https://github.com/D7x7z49/llm-api-scope/commit/012307954c03b06fe5b367581ee18c4821c8327e))

- **apiscope**: Reserve the source name all
  ([`2c4b094`](https://github.com/D7x7z49/llm-api-scope/commit/2c4b094f18e9b5ffa93c58c387f0011bf2fe9015))

- **config**: Allow local source overrides
  ([`49f6bba`](https://github.com/D7x7z49/llm-api-scope/commit/49f6bbae5466cafaaaa3bc6ce0801dc52b9c57d8))

- **errors**: Add message catalog errors
  ([`5bcc4a9`](https://github.com/D7x7z49/llm-api-scope/commit/5bcc4a98d747cbba6328a4e600e247721a4bbfa1))

- **list**: List effective sources
  ([`5d5900f`](https://github.com/D7x7z49/llm-api-scope/commit/5d5900f424158ced65ec4cf63a36c8faf01113ef))

- **list**: Window the source list by limit and offset
  ([`087ba63`](https://github.com/D7x7z49/llm-api-scope/commit/087ba6314062460cfc16df0af616cab61335492b))

- **output**: Add a text and json report pipeline
  ([`735a0d4`](https://github.com/D7x7z49/llm-api-scope/commit/735a0d4dfd250f5ebbd99934992704f717d6b352))

- **read**: Read leaf content by address and index
  ([`1bdf9da`](https://github.com/D7x7z49/llm-api-scope/commit/1bdf9dad515187db82cc7f35e871f7f080e9db09))

- **remove**: Remove registered sources
  ([`e9106f4`](https://github.com/D7x7z49/llm-api-scope/commit/e9106f4f55b763ae922bd11297f7172ccd99935a))

- **sync**: Add source synchronization runtime
  ([`c889836`](https://github.com/D7x7z49/llm-api-scope/commit/c8898368dc5279c23b793df5cabf91e87c409f59))

- **sync**: Preflight source dependencies
  ([`7a415ab`](https://github.com/D7x7z49/llm-api-scope/commit/7a415abed7bdc620b9e9ce724dfca0745414abff))

- **view**: Add cached source tree view
  ([`2529cd5`](https://github.com/D7x7z49/llm-api-scope/commit/2529cd54cdb12189efd2e6811cab3d5e6f752be2))

- **view**: Add tree-based route navigation
  ([`d10cf4c`](https://github.com/D7x7z49/llm-api-scope/commit/d10cf4c52aecc70748ca341e328a7fed3247ecd5))

- **view**: Anchor the scope root and add a depth cap
  ([`7dce0bc`](https://github.com/D7x7z49/llm-api-scope/commit/7dce0bce68f44d2a5e6dc97e6ddf27f3e7bcc635))

### Refactoring

- Restart implementation from archived baseline
  ([`fdfaf75`](https://github.com/D7x7z49/llm-api-scope/commit/fdfaf75af9f3030877e9e3c3e46552d6f4f3cb75))

- Separate command context and preflight concerns
  ([`f09ae9d`](https://github.com/D7x7z49/llm-api-scope/commit/f09ae9d2c1e0c380090585c70c8b53bb96292a0d))

- Unify source parsing and projection errors
  ([`deb1d3f`](https://github.com/D7x7z49/llm-api-scope/commit/deb1d3fef129edd788b19ac9d9494d266c79e8a3))

- **apiscope**: Centralize output text and share the content resolver
  ([`cb8eaa2`](https://github.com/D7x7z49/llm-api-scope/commit/cb8eaa22b6098682a0b636566d51d2a24f61b4fc))

- **apiscope**: Derive the report scope from the runtime context
  ([`cedd076`](https://github.com/D7x7z49/llm-api-scope/commit/cedd076ac37773b80fc05070314a69ba3d062978))

- **apiscope**: Keep read commands read-only
  ([`ebb2808`](https://github.com/D7x7z49/llm-api-scope/commit/ebb280842adbb60a88412830a91a22ccaf931951))

- **apiscope**: Select sync sources by a shared selector
  ([`4e14842`](https://github.com/D7x7z49/llm-api-scope/commit/4e14842d079a51acb53d868bb8f02a96b6356750))

- **apiscope**: Share the usage renderer
  ([`9fbc088`](https://github.com/D7x7z49/llm-api-scope/commit/9fbc088bbc63ec9301b56d39fe7a6d32576821cd))

- **cache**: Move cache mechanism to global module
  ([`b83c566`](https://github.com/D7x7z49/llm-api-scope/commit/b83c56603ad5dd51b0dad56326eb529aa4c11172))

- **config**: Harden persistence and merge rules
  ([`2a9287f`](https://github.com/D7x7z49/llm-api-scope/commit/2a9287f0e74f6f296a5c8d00149903388ffe9095))

- **config**: Prepare strict runtime configuration
  ([`e74adcd`](https://github.com/D7x7z49/llm-api-scope/commit/e74adcd956abe270646a61a02beab7339239d7ab))

- **context**: Add scoped runtime options and paths
  ([`5ca43d2`](https://github.com/D7x7z49/llm-api-scope/commit/5ca43d2da23819b1882da3cc251d577995cc0d4d))

- **context**: Share config paths across scopes
  ([`2d631f3`](https://github.com/D7x7z49/llm-api-scope/commit/2d631f3b76c229bb1c7b64157a1983729f4cee42))

- **gitignore**: Reduce source comment noise
  ([`c722000`](https://github.com/D7x7z49/llm-api-scope/commit/c722000c7f373b1132801702e204daa1f6217c5d))

- **view**: Key source trees and flatten view output
  ([`44a4ee2`](https://github.com/D7x7z49/llm-api-scope/commit/44a4ee22a84a71ee36369137c34240755695fcd9))

- **view**: Take one address like read
  ([`b504540`](https://github.com/D7x7z49/llm-api-scope/commit/b504540e67a3f68bb4c681e1dd5bb1ac16af9a00))

### Testing

- **sync**: Restore the openapi and rfc fetcher cases
  ([`7da547e`](https://github.com/D7x7z49/llm-api-scope/commit/7da547e7c19a15645ff0a5b25e60220129ff41f2))


## v0.8.0 (2026-06-11)

### Documentation

- Add skill section to readme
  ([`667a818`](https://github.com/D7x7z49/llm-api-scope/commit/667a8185bdaf8d0125708334752ab87c52ba4651))

### Features

- **skill**: Add install subcommand to export SKILL.md for code agents
  ([`2872127`](https://github.com/D7x7z49/llm-api-scope/commit/28721273cc920d707c304d8c5a890dea10e08574))


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
