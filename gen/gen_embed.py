import json, os, random, sys, base64
SEED, NT, NC, OUT = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
R = random.Random(SEED); os.makedirs(OUT, exist_ok=True)
BASIC = ["int", "string", "*int", "[]int", "bool", "*string"]
NAMES = ["A", "B", "Name", "X", "ID"]
TAGN = [None, None, "a", "A", "name", "x", "id", "-"]
types = []
for i in range(NT):
    fields = []
    for k in range(R.randint(1, 4)):
        tn = R.choice(TAGN)
        tag = None if tn is None else tn + (",omitempty" if R.random() < .2 else "")
        fields.append((R.choice(NAMES), R.choice(BASIC), tag, False))
    if i > 0:
        for _ in range(R.randint(0, 2)):
            j = R.randrange(i); t = R.choice([f"T{j}", f"*T{j}"])
            tag = None if R.random() < .8 else R.choice(["e", "-", ""])
            fields.append((None, t, tag, True))
    seen=set(); fl=[]
    for f in fields:
        key=f[0] if not f[3] else f[1].lstrip('*')
        if key in seen: continue
        seen.add(key); fl.append(f)
    types.append((f"T{i}", fl))
src = ['package main', '', 'import (', '\t"encoding/json"', '\t"math/rand"', '\t"reflect"', '\t"strconv"', '\t"strings"', '\t"time"', ')', '',
       'var _ = strconv.Itoa', 'var _ = strings.ToUpper', 'var _ time.Time', 'var _ = rand.Int', '',
       'var ifaceFillers = map[reflect.Type]func(reflect.Value, *rand.Rand){}', '']
for name, fields in types:
    src.append(f"type {name} struct {{")
    for g, t, tag, emb in fields:
        tg = f' `json:"{tag}"`' if tag is not None else ""
        src.append(f"\t{t}{tg}" if emb else f"\t{g} {t}{tg}")
    src.append("}")
src.append("var factories = []func() any{")
for name, _ in types: src.append(f"\tfunc() any {{ return new({name}) }},")
src += ["}", "var _ = json.Marshal"]
open(os.path.join(OUT, "types.go"), "w").write("\n".join(src) + "\n")
tmap = dict(types)
def keys_of(t, d=0):
    out = []
    for g, ft, tag, emb in tmap[t]:
        if emb:
            if d < 3 and (tag is None or tag == ""): out += keys_of(ft.lstrip('*'), d + 1)
            elif tag not in (None, "-", ""): out.append(tag)
            continue
        if tag == "-": continue
        out.append(tag.split(",")[0] if tag else g)
    return out
def val(): return R.choice([1, "s", None, [1, 2], True, "x"])
with open(os.path.join(OUT, "cases.tsv"), "w") as f:
    cid = 0
    for i, (name, _) in enumerate(types):
        ks = keys_of(name) + ["a", "A", "x", "name", "e", "zz"]
        for _ in range(NC):
            o = {}
            for _ in range(R.randint(1, 6)):
                k = R.choice(ks); k = k.swapcase() if R.random() < .2 else k
                o[k] = val() if R.random() < .8 else {R.choice(ks): val()}
            s = json.dumps(o)
            if R.random() < .2 and o:
                k = R.choice(list(o)); s = s[:-1] + ',' + json.dumps(k) + ':' + json.dumps(val()) + '}'
            for mode in ("fresh", "prefill"):
                f.write(f"{cid}\t{i}\t{mode}\t{base64.b64encode(s.encode()).decode()}\n"); cid += 1
        for seed in range(NC):
            f.write(f"{cid}\t{i}\tmarshal\t{seed}\n"); cid += 1
print("types", NT, "cases", cid)
