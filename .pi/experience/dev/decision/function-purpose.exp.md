<!-- .pi/experience/dev/decision/function-purpose.exp.md -->
<!-- NOTE: classify a function by purpose before choosing where it lives. -->

STEP.
- split a function's purpose into two kinds: decomposition and reuse
- treat a decomposition function as a local unit that names one step and lowers the caller's complexity
- keep a decomposition function private and in its owning file, even when it runs once
- treat a reuse function as the single home for logic that appears identically in several scopes
- place a reuse function at a boundary shared by its callers
- let reuse stay passive, and extract it only after two or more identical instances exist
- ask which kind a function is before choosing its scope
- leave a repeated shape local when the instances differ in intent
- keep a reuse function free of behavior flags and mode parameters
- judge an extraction by the context a reader must load, not by the lines it removes

NOTE.
- decomposition serves complexity, readability, and local reasoning
- reuse serves maintainability and one authoritative source
- reuse accumulates from decomposition, so it follows rather than leads
- an active reuse function raises complexity and lowers maintainability
- identical text can carry different knowledge, so merge knowledge and not characters
- a shape behind a behavior flag is an organizing need in reuse clothing
- a reusable boundary is discovered from the tree, not drawn up front
- use this lens before abstraction, and keep it a lens, not a ban

---
