<!-- .pi/experience/dev/decision/fractal-scope-design.exp.md -->
<!-- NOTE: preserve bounded local reasoning across scales. -->

STEP.
- represent a complex system as nested scopes with stable boundaries
- give each scope a small contract that states purpose, owned state, inputs, outputs, invariants, and failure boundary
- repeat the contract shape at each scale so a known local pattern remains useful in a new scope
- keep each scope understandable from its own contract, parent contract, and small explicit neighborhood
- use stable names, order, and layout so structure provides a cheap address and global index
- keep implementation details inside their owning scope and expose only the boundary needed by neighboring scopes
- make cross-scope dependencies explicit, directed, and few
- let local rules and local state produce larger behavior through composition rather than hidden global coordination
- inspect the structure first, then load the active scope and only the details required by the task
- change and validate the active scope locally, then check its boundary effects
- preserve the same navigation, contract, and validation pattern as the system grows

NOTE.
- this principle combines boundary-based decomposition, self-similar organization, and bounded local interaction
- use the principle when people or agents must work with limited active context
- treat structure as a compression of location, ownership, order, and inheritance
- distinguish self-similarity from fragmentation; repeated layout alone is not a useful contract
- do not force a recursive shape onto a domain that has no repeated local structure
- treat hidden state, arbitrary ancestor access, and untracked exceptions as breaks in locality
- keep the active rule set small, but do not claim that total domain complexity or total work becomes constant
- prefer a stable pattern that supports discovery and safe local change over a clever pattern that saves local code
- keep this as a design lens, not a requirement for every system

---
