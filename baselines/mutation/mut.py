import random, base64, json, sys
R = random.Random(int(sys.argv[1])); N = int(sys.argv[2])
seeds = {
 0: {"id": 7, "name": "Ann", "email": "a@b.c", "score": 1.5, "active": True, "tags": ["x", "y"], "meta": {"k": 1, "n": None}, "created": "2020-01-02T03:04:05Z", "parent": {"id": 1}, "raw": {"z": [1, 2]}, "attrs": {"a": "b"}},
 1: {"kind": "click", "count": 12, "ratio": 0.5, "level": 3, "items": [{"sku": "A1", "price": 9.99, "qty": 2}], "at": "2021-06-01T00:00:00Z", "extra": [1, "two"]},
 2: {"name": "svc", "port": "8080", "debug": False, "limits": {"cpu": 2}, "servers": ["a", "b"], "num": 12.5},
 3: {"a": 1, "b": [True, None], "c": {"d": "e"}},
 4: [1, "s", None, {"k": [2]}],
 5: {"x": "y", "z": ""},
 6: [1, 2, 3],
 7: {"sku": "B", "price": 1, "qty": 3},
}
TOK = ['null', 'true', '1e400', '-0', '1e39', '"\\u0000"', '"\xff"', '[]', '{}', '"null"', '18446744073709551616', '0.1', '"2020-01-02"', '""', '-1']
def mutate(s):
    b = list(s)
    for _ in range(R.randint(1, 4)):
        r = R.random()
        if r < 0.25 and b: i = R.randrange(len(b)); b[i] = chr(R.randrange(32, 127))
        elif r < 0.45 and b: i = R.randrange(len(b)); del b[i]
        elif r < 0.75:
            # replace a value token after a colon
            s2 = ''.join(b); idx = [i for i, ch in enumerate(s2) if ch == ':']
            if idx:
                i = R.choice(idx) + 1; j = i
                while j < len(s2) and s2[j] not in ',}]': j += 1
                s2 = s2[:i] + ' ' + R.choice(TOK) + s2[j:]
            b = list(s2)
        elif r < 0.85:
            s2 = ''.join(b); k = R.choice(['"id"', '"name"', '"port"', '"a"', '"kind"', '"x"'])
            s2 = s2.replace(k, k.upper() if R.random() < .5 else k, 1); b = list(s2)
        else:
            s2 = ''.join(b)
            if s2.endswith('}') and len(s2) > 2: s2 = s2[:-1] + ',' + s2[1:-1].split(',')[0] + '}'
            b = list(s2)
    return ''.join(b)
cid = 0
for n in range(N):
    t = R.randrange(len(seeds)); s = json.dumps(seeds[t], ensure_ascii=False)
    s = mutate(s)
    for mode in ("fresh", "prefill"):
        print(f"{cid}\t{t}\t{mode}\t{base64.b64encode(s.encode('utf-8','surrogateescape')).decode()}"); cid += 1
    print(f"{cid}\t{t}\tmarshal\t{n}"); cid += 1
