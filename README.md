# go-json-v2-difftest

Differential fuzzing of Go's `encoding/json` v1 emulation layer.

Since Go 1.27, `encoding/json` runs on the `encoding/json/v2` engine with options that emulate v1 behavior. Building with `GOEXPERIMENT=nojsonv2` restores the original v1 engine. This repository builds the same test program both ways, feeds both the same generated types and inputs, and reports every case where they disagree.

The tool compares:

- the Go type of the returned error (never the error text),
- the decoded value, into a fresh destination and into a prefilled one,
- the bytes written by `json.Marshal`.

Values are printed by a reflection dumper that does not use `encoding/json` and sorts map keys, so equal values print identically in both builds.

## Results

Found with this tool and filed:

| Issue | Behavior in Go 1.27 |
| --- | --- |
| [golang/go#83391](https://github.com/golang/go/issues/83391) | Map key types with UnmarshalJSON are decoded with UnmarshalText |
| [golang/go#83392](https://github.com/golang/go/issues/83392) | json.Number (and string-kind text types) with `,string` no longer unquote |
| [golang/go#83393](https://github.com/golang/go/issues/83393) | time.Time keeps its old value after a parse error |
| [golang/go#83395](https://github.com/golang/go/issues/83395) | Unmarshal continues after Unmarshaler, time or `,string` errors, where v1 stopped |

On go1.27.0 the v0 generator also finds 5 of 7 previously reported regressions within 0.4 seconds. Details are in [docs/](docs/).

## Requirements

- Go 1.27 or later (the script fetches the toolchain through `GOTOOLCHAIN`)
- Python 3

## Usage

```
./run.sh {v0|v1|embed|mutation} SEED NTYPES NCASES OUTDIR
```

- `v0`: random struct types over 34 field kinds and 8 tag variants.
- `v1`: adds 14 kinds (text-method types, interface embedding json.Marshaler, more map key types, and others) and 6 tag names.
- `embed`: struct embedding and field-name conflicts.
- `mutation`: byte-level mutation baseline over 8 fixed realistic types.

Set `SINGLE=1` with `v0` or `v1` to enumerate every field kind with every tag. Set `GOTOOLCHAIN` to test another Go version (default `go1.27.4`).

Examples:

```
./run.sh v0 1 200 4 out/v0
SINGLE=1 ./run.sh v1 1 0 60 out/v1-single
python3 triage/classify.py out/v1-single
GOTOOLCHAIN=go1.27.0 ./run.sh v0 2 400 4 out/v0-1270
```

`run.sh` prints the number of differing cases. `triage/classify.py` groups the differences of a single-field run by known cause and lists the rest for manual review.

## Layout

| Path | Contents |
| --- | --- |
| `gen/` | Type and input generators (v0, v1, embedding) |
| `harness/` | Go harness: reads cases on stdin, prints error type and dumped value |
| `baselines/mutation/` | Byte-level mutation baseline and its classifier |
| `triage/` | Auto-classifier for single-field runs |
| `repro/` | Minimal reproducers for each filed issue and for the known issues used in the recall study |
| `prevalence/` | go/ast scanner for the affected patterns, and the script that ran it on popular repositories |
| `docs/` | Pre-registration, recall and baseline results, ablation and prevalence results |

## Limits

- Error message text and error field contents are not compared.
- Some differences are intended v2 changes allowed by the release notes; check the `encoding/json` documentation before reporting one.
- The prevalence scanner is syntactic and over-counts; treat its numbers as an upper bound.

## License

MIT. See [LICENSE](LICENSE).
