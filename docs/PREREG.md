# Pre-registration: differential fuzzing of Go 1.27 encoding/json engines (written 2026-11-25, before any fuzz output)

## Claim
Generated Go types and JSON inputs, run through encoding/json in Go 1.27.4 built two ways (default, which uses the
v2 engine with v1 emulation; and GOEXPERIMENT=nojsonv2, the original engine), expose several distinct behavior
differences that are not error-text-only and are not yet reported on golang/go. The release notes say none should exist.

## Comparison (per case)
- Unmarshal into a fresh value: whether an error is returned, the error's Go type, and the decoded value
  (dumped by a reflection walker that follows pointers and sorts map keys; no use of encoding/json).
- Unmarshal into a pre-filled value: same fields.
- Marshal of a seeded random value: output bytes, whether an error is returned, the error's Go type.
- Error message text is never compared.

## Kill conditions (fixed now)
- K1: after 1 CPU hour per build, fewer than 3 distinct root causes of non-error-text differences.
- K2: every distinct root cause matches an already reported golang/go issue (open or closed) or a documented difference.
- K3: prior art already runs differential fuzzing of v1 against v2-backed v1.
- K4: instrument check fails: the same build run twice gives different outputs (nondeterminism).

## Root-cause counting
Each differing case is minimized by hand to the smallest type and input that still differs. Two cases share a root
cause if their minimized reproducers exercise the same decoder or encoder rule. Each root cause is searched on
golang/go issues (title and body search, open and closed).

## Predictions (priors)
- P1: 1% to 10% of cases differ.
- P2: 3 to 8 distinct root causes, of which 1 to 4 are unreported.
- P3: most differing cases involve map keys, embedded structs, the string tag option, or invalid UTF-8.

## Conveniences
- Generator includes exotic combinations real code rarely uses. Each root cause will be reported with a note on
  whether the feature combination appears in real modules (grep of the 80 modules from the earlier run).
- One platform (linux/amd64), one Go version (1.27.4). Root causes are rechecked on Go tip if it builds here.
