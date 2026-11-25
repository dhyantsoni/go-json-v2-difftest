"""Generate a Go program with N random struct types and a JSON case file for them.
Usage: python3 gen.py SEED NTYPES NCASES_PER_TYPE OUTDIR
"""
import json, os, random, sys, base64

SEED, NT, NC, OUT = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
R = random.Random(SEED)
os.makedirs(OUT, exist_ok=True)

PRIM = ["int", "int8", "uint8", "int64", "uint64", "float32", "float64", "string", "bool"]
SPECIAL = ["*int", "*string", "[]int", "[]byte", "[2]int", "map[string]int", "map[int]string",
           "map[float64]int", "map[KeyT]int", "map[KeyJ]int", "map[KeyJT]int", "any", "json.RawMessage",
           "json.Number", "time.Time", "CustomJ", "*CustomJ", "CustomPJ", "CustomT", "*CustomT", "[]any",
           "map[string]any", "*float64", "[]string", "uintptr"]
KINDS_STR = {"string", "*string", "CustomT", "*CustomT"}
NUMERIC = {"int", "int8", "uint8", "int64", "uint64", "float32", "float64", "*int", "*float64", "uintptr"}

types = []  # list of (name, fields) ; field = (gname, gotype, tag, embedded)

def ftype(i):
    r = R.random()
    if i > 0 and r < 0.18:
        j = R.randrange(i)
        return R.choice([f"T{j}", f"*T{j}", f"[]T{j}", f"map[string]T{j}"])
    if r < 0.6:
        return R.choice(PRIM)
    return R.choice(SPECIAL)

def mkname():
    return R.choice(["A", "B", "Name", "ID", "Value", "X", "Y", "Data", "Count", "Time", "Key", "Opt"])

SINGLE = os.environ.get("SINGLE") == "1"
ALLK = PRIM + SPECIAL
TAGS = [None, "a", "a,omitempty", "a,string", "a,omitzero", "-", "-,", ",omitempty,string"]
if SINGLE:
    combos = [(k, t) for k in ALLK for t in TAGS]
    NT = len(combos)
for i in range(NT):
    if SINGLE:
        k, t = combos[i]
        types.append((f"T{i}", [("F", k, t, False)])); continue
    fields = []
    used = set()
    for k in range(R.randint(1, 6)):
        t = ftype(i)
        embedded = False
        if i > 0 and R.random() < 0.15:
            j = R.randrange(i)
            t = R.choice([f"T{j}", f"*T{j}"]); embedded = True
        gname = mkname() + str(k) if not embedded else None
        tagname = None
        r = R.random()
        if r < 0.25: tagname = R.choice(["a", "A", "name", "Name", "x", "value", "id", "ID", "key"])
        elif r < 0.30: tagname = "-"
        opts = []
        if R.random() < 0.25: opts.append("omitempty")
        if R.random() < 0.10: opts.append("omitzero")
        if (t in NUMERIC or t in ("string", "bool")) and R.random() < 0.25: opts.append("string")
        tag = None
        if tagname is not None or opts:
            tag = (tagname or "") + "".join("," + o for o in opts)
            if tagname == "-" and R.random() < 0.5: tag = "-,"
        fields.append((gname, t, tag, embedded))
    types.append((f"T{i}", fields))

# ---- Go source
src = ['package main', '', 'import (', '\t"encoding/json"', '\t"strconv"', '\t"strings"', '\t"time"', ')', '',
       'var _ = strconv.Itoa', 'var _ = strings.ToUpper', 'var _ time.Time', '',
       '// KeyT: text-marshaled map key',
       'type KeyT struct{ S string }',
       'func (k KeyT) MarshalText() ([]byte, error) { return []byte("k:" + k.S), nil }',
       'func (k *KeyT) UnmarshalText(b []byte) error { k.S = strings.TrimPrefix(string(b), "k:"); return nil }',
       '// KeyJ: JSON-unmarshaler map key (no text methods of its own)',
       'type KeyJ struct{ S string }',
       'func (k *KeyJ) UnmarshalJSON(b []byte) error { k.S = "j:" + string(b); return nil }',
       '// KeyJT: both JSON and text methods',
       'type KeyJT struct{ S string }',
       'func (k *KeyJT) UnmarshalJSON(b []byte) error { k.S = "j:" + string(b); return nil }',
       'func (k *KeyJT) UnmarshalText(b []byte) error { k.S = "t:" + string(b); return nil }',
       'func (k KeyJT) MarshalText() ([]byte, error) { return []byte("t:" + k.S), nil }',
       'type CustomJ struct{ N int }',
       'func (c CustomJ) MarshalJSON() ([]byte, error) { return []byte(strconv.Itoa(c.N)), nil }',
       'func (c *CustomJ) UnmarshalJSON(b []byte) error { n, err := strconv.Atoi(string(b)); c.N = n; return err }',
       'type CustomPJ struct{ N int }',
       'func (c *CustomPJ) MarshalJSON() ([]byte, error) { return []byte(`"p` + strconv.Itoa(c.N) + `"`), nil }',
       'type CustomT struct{ S string }',
       'func (c CustomT) MarshalText() ([]byte, error) { return []byte(strings.ToUpper(c.S)), nil }',
       'func (c *CustomT) UnmarshalText(b []byte) error { c.S = strings.ToLower(string(b)); return nil }',
       '']
for name, fields in types:
    src.append(f"type {name} struct {{")
    for gname, t, tag, emb in fields:
        tg = f' `json:"{tag}"`' if tag is not None else ""
        if emb: src.append(f"\t{t}{tg}")
        else: src.append(f"\t{gname} {t}{tg}")
    src.append("}")
src.append("")
src.append("var factories = []func() any{")
for name, _ in types: src.append(f"\tfunc() any {{ return new({name}) }},")
src.append("}")
src.append("var _ = json.Marshal")
open(os.path.join(OUT, "types.go"), "w").write("\n".join(src) + "\n")

# ---- JSON inputs
def jval(t, depth=0):
    tmap = dict((n, f) for n, f in types)
    if depth > 3: return None
    if t.startswith("*"): return None if R.random() < 0.2 else jval(t[1:], depth)
    if t in ("int", "int8", "uint8", "int64", "uint64", "uintptr"): return R.choice([0, 1, -1, 127, 255, 300, -129, 2**53, 1e3, 1.5, 18446744073709551615])
    if t in ("float32", "float64"): return R.choice([0, 1.5, -2.25, 1e38, 3.5e38, 1e308, 1e-320])
    if t == "string": return R.choice(["", "a", "Hello", "ünï", " ", "<b>&", "123", "true", "null"])
    if t == "bool": return R.choice([True, False])
    if t.startswith("[]") or t.startswith("[2]"):
        inner = t[2:] if t.startswith("[]") else t[3:]
        if inner == "byte": return R.choice(["AQID", "", "!!", None])
        return [jval(inner, depth + 1) for _ in range(R.randint(0, 3))]
    if t.startswith("map["):
        kt, vt = t[4:].split("]", 1)
        keys = {"string": ["a", "b", ""], "int": ["1", "-2", "x", "01"], "float64": ["1.5", "1e2", "x", "null"],
                "KeyT": ["k:a", "b"], "KeyJ": ["2018-12-12", "a"], "KeyJT": ["q", "r"]}[kt]
        return {R.choice(keys): jval(vt, depth + 1) for _ in range(R.randint(0, 3))}
    if t in ("any", "json.RawMessage"): return R.choice([1, "s", None, [1, "a"], {"k": 2}, 1.25])
    if t == "json.Number": return R.choice([12, "12", 1.5e3, "x"])
    if t == "time.Time": return R.choice(["2020-01-02T03:04:05Z", "2020-01-02", 5])
    if t in ("CustomJ", "CustomPJ"): return R.choice([7, "7", None])
    if t == "CustomT": return R.choice(["HeLLo", 3])
    if t in tmap:
        o = {}
        for gname, ft, tag, emb in tmap[t]:
            key = gname
            if tag and tag.split(",")[0] not in ("", "-"): key = tag.split(",")[0]
            if emb:
                sub = jval(ft.lstrip("*"), depth + 1)
                if isinstance(sub, dict): o.update(sub)
                continue
            if key is None: continue
            v = jval(ft, depth + 1)
            if tag and ",string" in tag and v is not None and not isinstance(v, (list, dict)): v = json.dumps(v)
            o[key] = v
        return o
    return None

def mutate(s, obj):
    r = R.random()
    if r < 0.15 and isinstance(obj, dict) and obj:
        k = R.choice(list(obj)); return s.replace(json.dumps(k), json.dumps(k.swapcase()), 1)
    if r < 0.25 and isinstance(obj, dict) and obj:
        k = R.choice(list(obj)); return s[:-1] + ("," if len(obj) else "") + json.dumps(k) + ":" + json.dumps(R.choice([1, "z", None, [], {}])) + "}"
    if r < 0.32: return s.replace("\"a\"", "\"a\xff\"", 1)
    if r < 0.38: return s + " "
    if r < 0.42: return s.replace(":", ":null,\"zz\":", 1) if ":" in s else s
    if r < 0.48 and isinstance(obj, dict) and obj:
        k = R.choice(list(obj)); return s[:-1] + ("," if len(obj) else "") + json.dumps(k) + ":" + json.dumps(R.choice([True, 3, "q", [1]])) + "}"
    return s

with open(os.path.join(OUT, "cases.tsv"), "w") as f:
    cid = 0
    for i, (name, _) in enumerate(types):
        for _ in range(NC):
            obj = jval(name)
            s = json.dumps(obj, ensure_ascii=False)
            s = mutate(s, obj)
            for mode in ("fresh", "prefill"):
                f.write(f"{cid}\t{i}\t{mode}\t{base64.b64encode(s.encode('utf-8', 'surrogateescape')).decode()}\n"); cid += 1
        for seed in range(NC):
            f.write(f"{cid}\t{i}\tmarshal\t{seed}\n"); cid += 1
print("types", NT, "cases", cid)
