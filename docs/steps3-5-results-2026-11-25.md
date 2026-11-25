# Go encoding/json v2 fuzzing: longer runs, feature ablation, real-code prevalence (2026-11-25)

All on go1.27.4, linux/amd64. Differences are between the default build and GOEXPERIMENT=nojsonv2.

## Step 3. Longer runs (generator v1) and triage

Generator v1 adds generic features to v0: string-kind and int-kind named types with text methods, a string type with MarshalJSON, an interface embedding json.Marshaler, uint64 and int8 map keys, double pointers, pointer slices, byte arrays, RawMessage pointers and maps, and tag names with punctuation. (v0 recall numbers in the earlier report are unaffected; v1 was written after the recall list was known.)

Single-field round: 672 types (48 kinds x 14 tag variants), 40,320 cases, 2,924 differences.

| Class | Cases | Status |
|---|---|---|
| Error Go type only | 683 | excluded (release notes allow error differences) |
| Map key types with UnmarshalJSON | 651 | #83391 (filed) |
| Marshal of float64-key maps or struct-key maps: v1 error, v2 writes output | 315 | #81373 (float keys); #79938 (arbitrary key types, closed not planned) |
| Float64 map keys accepted on Unmarshal | 305 | #81373 |
| Invalid UTF-8 written as literal U+FFFD | 271 | #82685 |
| time.Time keeps old value after error | 169 | #83393 (filed) |
| "null" as numeric map key | 126 | #82872 (fixed on tip) |
| Marshal panic: interface embedding Marshaler with nil pointer | 86 | #82682 (fixed on tip) |
| json.Number with ,string | 44 | #83392 (filed) |
| Untriaged after auto-classification | 274 | triaged by hand below |

Hand triage of the 274:
- Most are the error path of #83395 (filed): after an error from UnmarshalText on a map key, from a custom UnmarshalJSON, or from ,string, v1 stops and v2 continues. Duplicate object names make this visible on single fields too.
- Interface field holding a typed nil pointer, after a type error: v1 keeps the old (*T)(nil), v2 sets nil. Same error-path family as #83393.
- NEW VARIANT: the ,string option on a string-kind type with UnmarshalText. go1.26.8: `"\"x\""` is unquoted and UnmarshalText gets `x`. go1.27.4 and tip: UnmarshalText gets the quoted text. A named string type without methods and a plain string are unaffected. This is most likely the same root cause as #83392 (json.Number): the ,string unquoting step is skipped for string-kind types with special decoding. Reproducer: repro/string-option-text-types/main.go. Suggested action: add as a comment on #83392, not a new issue.

Embedding round (5 seeds x 120 types, struct embedding and field-name conflicts, plain field kinds only, 21,600 cases): 694 differences. 684 are U+FFFD in Marshal output (#82685). 10 are the error-path family: after a type error the v2 emulation allocates an embedded pointer struct that v1 left nil. No new root cause from embedding or name resolution.

## Step 4. Feature ablation (single-field round, semantic differences only)

Share of cases with a difference that is not error-type-only and not the U+FFFD bug:

| Field kind | Share |
|---|---|
| map[float64]int | 77.7% |
| map key type with UnmarshalJSON (KeyJ) | 48.8% |
| map key type with UnmarshalJSON and UnmarshalText (KeyJT) | 39.8% |
| interface embedding json.Marshaler | 16.5% |
| time.Time | 11.5% |
| string-kind type with text methods (SKT) | 9.0% |
| map with int-kind text-method keys | 7.9% |
| int-kind type with text methods (IKT) | 6.9% |
| json.Number | 2.1% |
| type with UnmarshalJSON (value / pointer) | 1.2% / 1.0% |
| 37 other kinds (all basic kinds, slices, arrays, pointers, string/int-keyed maps, RawMessage, any, types with only Marshal methods) | 0% |

By tag option: ,string 7.7%; omitempty 6.0%; omitzero 4.0%; no option 3.9%.

Reading: the v1 emulation matches v1 for every plain kind tested. All differences sit where v1 had special rules: custom decoding methods (on values and on map keys), time.Time, json.Number, the ,string option, and float keys.

## Step 5. Prevalence in real code (main-module source of the 80 test-suite modules, non-test files, syntactic scan)

| Pattern | Bug | Modules | Occurrences |
|---|---|---|---|
| Map key type that declares UnmarshalJSON | #83391 | 1 / 80 (easyjson) | 2 |
| json.Number field with ,string | #83392 | 0 / 80 | 0 |
| Text-method type field with ,string | #83392 variant | 0 / 80 | 0 |
| Any ,string tag | exposure | 1 / 80 | 13 |
| Interface embedding json.Marshaler or Unmarshaler | #82682 | 0 / 80 | 0 |
| map[float32/float64] | #81373 | 1 / 80 (go-kit) | 1 |
| time.Time field in a json-tagged struct | #83393, #83395 exposure | 14 / 80 (17.5%) | 382 |
| Field whose type declares UnmarshalJSON or UnmarshalText | #83395 exposure | 16 / 80 (20.0%) | 200 |

Reading: the map-key, json.Number, float-key and interface bugs need patterns that are rare in this sample, which fits the test-suite run finding almost nothing. The error-path bugs (#83393, #83395) sit on patterns that 1 in 5 modules use, but they only show when input is invalid, which ordinary test suites rarely feed. This explains why ecosystem test suites missed them and generated inputs did not.

Limits: 80 modules, main module only (dependencies not scanned), syntactic match without type checking (a type declared in another module is not seen), exposure is not proof of an observable bug.
