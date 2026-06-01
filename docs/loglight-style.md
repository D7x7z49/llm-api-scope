<!-- docs/loglight-style.md -->
<!-- A lightweight script logging convention for short-lived automation scripts. -->

MARKERS
- Boundary markers frame sections.
  - start = `[=]`, name, `Start` ;
  - end   = `[=]`, name, `Complete` ;
- Process markers report discrete steps.
  - `[-]`, verb phrase ;
- Interaction markers show ongoing work.
  - `[*]`, description, [`...`] ;
- Discovery markers report positive finds or creations.
  - `[+]`, description ;
- Error markers signal critical problems.
  - `[!]`, description ;
- Warning markers signal non-critical issues.
  - `[?]`, description ;

NESTING
- Markers assume sequential execution with guaranteed output ordering.
- Under concurrency or asynchronous execution boundary markers are unreliable.
- Markers nest in a fixed order: boundary then process then interaction then status.
- Status markers encompass discovery, error, and warning as siblings.
- Maximum three levels of nesting.
- Indent with two spaces per level.

RULES
- Every `[=] Start` must have a matching `[=] Complete` with the same name.
- Messages stay short and specific with exact quantities where possible.
- Use ASCII characters only.
- Separate major sections with a blank line.
- Group related steps without blank lines.

CONTEXT
- Suitable for one-time scripts, quick automation, test runners, setup scripts, and diagnostic tools.
- Unsuitable for long-running services, production systems, high-frequency logging, machine-parsed logs, and audit logs.
- Unsuitable when output ordering is not guaranteed under concurrency or asynchronous execution.

---
