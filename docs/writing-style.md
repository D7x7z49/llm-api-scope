<!-- docs/writing-style.md -->
<!-- Project writing conventions for code comments, error messages, and documentation. -->

CASE
- All natural language text uses lowercase.
- Abbreviations and proper names retain their conventional case.
- File header comments use lowercase with `/` as path separator.
  - header_path = `#`, path, eol ;
  - path = segment, {`/`, segment} ;

DELIMITERS
- Wrap local identifiers in square brackets.
  - path, alias, key, variable name.
- Wrap external references in angle brackets.
  - URL, upstream link.
- Use parentheses for supplementary or clarifying information.

PROSE
- Write in natural English word order.
- Use prepositions as needed to connect context to values.
- End a sentence with a period only when it forms a complete statement.
  List items, short notes, and fragment messages omit the trailing period.

STRUCTURE
- Use an ALL CAPS word on its own line to introduce a section.
- Section body follows on indented lines or as a dashed list.
- A single topic uses one indented paragraph.
- Multiple rules use a dashed list.

PRECEDENCE
- CASE governs the shape of every word.
- DELIMITERS and PROSE together govern how words combine into text.
- STRUCTURE governs how text blocks combine into documents and is independent of inline rules.

---
