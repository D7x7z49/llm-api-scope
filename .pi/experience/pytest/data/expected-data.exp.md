<!-- .pi/experience/pytest/data/expected-data.exp.md -->
<!-- NOTE: leave a clear and kind oracle for the future self who will read the failure. -->

STEP.
- begin with the behavior under test, then choose the expected-data form that makes it easiest to understand
- keep a small stable value close to the test so the future reader can see the promise immediately
- compare mappings and sequences directly so pytest can show a helpful difference
- parse JSON, YAML, and similar output before comparing it when formatting is not part of the promise
- compare complete text when whitespace, ordering, separators, or line layout are part of the promise
- use `pytest.mark.parametrize` when one behavior has several input and expected-output pairs
- keep each parameter set about the same behavior and give important cases readable ids
- use `pytest.approx` with an explicit tolerance when a numeric result is naturally approximate
- use `pytest.raises` for an expected exception, then check the stable fields or message pattern that matters
- use a fixture for a shared expected value when its ownership and contract are clear
- use a factory fixture when one test needs several independent records
- place large, stable test vectors in a nearby data file and parse them into clear expected values
- keep expected data independent from the serializer, merger, or builder that creates the actual value
- compare the fields that define the promise and leave incidental representation details alone
- shape every assertion so a failure helps the next reader find the repair

NOTE.
- let the expected value explain why the behavior matters, not only what the code currently returns
- keep shared expected data small and intentional; local values are often kinder to the reader
- remember that parametrized lists and mappings are passed without copying, so give each case its own data when mutation is possible
- use an exact text comparison when the complete output is the user-facing contract
- parse serialized JSON before comparing it when key order and whitespace carry no meaning
- preserve ordering, fields, or normalization only when the product promise gives them meaning
- choose a snapshot or golden file when a large exact output is truly the promise and reviewing changes will remain comfortable
- prefer an explicit expected value over a generated one that could repeat the same mistake
- when changing expected data, explain the changed promise through the test name or nearby setup

---
