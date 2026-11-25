# Go encoding/json v2 fuzzing: recall and baselines (2026-11-25)

All runs on linux/amd64, 2 CPU cores. "Engine difference" = output of the default build differs from the GOEXPERIMENT=nojsonv2 build of the same program on the same input. Error message text is never compared.

## 1. Recall on Go 1.27.0

Ground truth: closed or confirmed golang/go issues about v1-compatibility of json.Marshal / json.Unmarshal under Go 1.27, each checked with a minimal program to show an engine difference on go1.27.0. (Source: GitHub search of closed encoding/json issues created after 2026-06-01, 81 results, plus the Go1.27.1 and Go1.27.2 backport milestones.)

Excluded from the denominator, with reason:
- Outside Marshal/Unmarshal: #80999 and #81853 (Decoder), #81547 (MarshalIndent), #81050 (fmt printing).
- Error-field contents only, which the oracle does not compare by design: #81176, #82079, #83176.
- Documentation or v2-only API: #80995, #80114, #80117.
- User error: #80733.
- Reproducer did not show a difference on 1.27.0 with my inputs: #81383, #81297. Not counted either way.

| Issue | Behavior | Differs on 1.27.0 | Fixed by | Found by generator (v0, written before this list was compiled) | Found by byte-level baseline |
|---|---|---|---|---|---|
| #81061 | quoted "null" with ,string on a string field | yes | 1.27.1 | yes (round 1, case 36) | no |
| #81062 | float32 overflow leaves +Inf | yes | 1.27.2 | yes (round 2, 0.12 s) | yes |
| #81373 | float64 map keys accepted | yes | not fixed on tip | yes (0.38 s) | no (no numeric-key map types) |
| #82685 | invalid UTF-8 written as literal U+FFFD | yes | not fixed on tip | yes (0.17 s) | yes |
| #82872 | object name "null" as zero numeric map key | yes | tip | yes (0.38 s) | no |
| #81355 | MarshalText honored for string-kind map keys | yes | 1.27.2 | no (no string-kind key type with MarshalText) | no |
| #82682 | Marshal panic, nil pointer in interface embedding Marshaler | yes | tip | no (no such interface type) | no |

Recall: generator 5 of 7 (71%); byte-level baseline 2 of 7 (29%). All generator detections came within the first 0.4 s of runtime (about 125 microseconds per case for both builds together).

## 2. Baselines

| Method | Budget | Cases | Engine differences | Known issues found (of 7) | Unreported regressions found |
|---|---|---|---|---|---|
| Type generator, rounds 1 and 2 | about 1 s | 9,228 | 805 + 545 (1.27.4); more on 1.27.0 | 5 | 4: #83391, #83392, #83393, and stop-vs-continue (below) |
| Byte-level mutation, 8 fixed realistic types, same oracle | about 10 s | 99,000 | 5,938 | 2 | 2: #83393 (time.Time keeps old value) and stop-vs-continue |
| Go's own FuzzUnmarshalJSON (single engine, round trip) | 300 s | 490,741 execs | n/a | 0 | 0 |
| Go's own FuzzDecoderToken | 301 s | about 860,000 execs | n/a | 0 | 0 |
| Test suites of 80 popular modules (run on 1.27.4) | about 4 h | 87,962 tests | 1 confirmed | 1 (#82685) | 0 |

Reading: the in-tree fuzzers cannot see these bugs because they test one engine against itself. Byte-level differential fuzzing finds the bugs reachable from common types. Type generation finds the bugs that need specific type shapes (map key types, json.Number with ,string, numeric map keys), which is where most of the Go 1.27 regressions are.

## 3. New regression found during this step (not yet filed)

On errors returned by an Unmarshaler method (including time.Time's) and by the ,string option, Go 1.26 and go1.27.4 with nojsonv2 stop decoding, so later fields stay empty. go1.27.4 default and tip continue and fill the later fields. Plain type mismatches behave the same in both (decoding continues, as documented).

```
go1.26.8 / 1.27.4 nojsonv2      go1.27.4 / tip
time.Time error:     B=""       B="after"
,string error:       B=""       B="after"
UnmarshalJSON error: B=""       B="after"
type mismatch:       B="after"  B="after"   (control)
```

Reproducer: repro/stop-vs-continue/main.go. Not found in issue searches; the nearest is #82870, which is about the Struct/Field context in UnmarshalTypeError, not about decoding continuing. Related to #83393 (same error path, different symptom). Found by both the generator (round 1, case 90) and the byte-level baseline.

## Limits
- Ground truth is limited to issues someone reported; bugs nobody reported cannot be counted in recall.
- One platform, 2 cores, short budgets. Equal-time comparison is approximate: the generator needed far less time than the others were given.
- The byte-level baseline's type set was chosen by me; a different set would find different bugs.
