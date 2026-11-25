import re,base64,sys,json
def run(d):
    types={}
    for m in re.finditer(r'type T(\d+) struct \{\n\tF (\S+)(?: `json:"([^"]*)"`)?\n\}', open(f'{d}/types.go').read()):
        types[int(m.group(1))]=(m.group(2), m.group(3) or '')
    cases=[l.rstrip('\n').split('\t') for l in open(f'{d}/cases.tsv')]
    a=[l.rstrip('\n').split('\t',1)[1] for l in open(f'{d}/v1.out')]; b=[l.rstrip('\n').split('\t',1)[1] for l in open(f'{d}/v2.out')]
    first={}; count={}
    for i,c in enumerate(cases):
        if a[i]==b[i]: continue
        k,t=types[int(c[1])]; mode=c[2]; opts=t.split(',')[1:]
        inp=base64.b64decode(c[3]).decode('utf-8','replace') if mode!='marshal' else ''
        hits=[]
        if k=='string' and 'string' in opts and mode!='marshal' and '\\"null\\"' in inp.replace(' ',''): hits.append('81061')
        if k=='float32' and mode!='marshal' and 'Inf' in b[i] and 'Inf' not in a[i]: hits.append('81062')
        if 'map[float64]' in k and mode!='marshal' and '"null"' not in inp: hits.append('81373')
        if mode=='marshal' and '\\ufffd' in a[i] and '�' in b[i]: hits.append('82685')
        if mode!='marshal' and ('map[float64]' in k or 'map[int' in k) and '"null"' in inp: hits.append('82872')
        for h in hits:
            count[h]=count.get(h,0)+1; first.setdefault(h,i)
    return len(cases),first,count
root=sys.argv[1] if len(sys.argv)>1 else "out/seeds"
res={}
for s in range(1,11):
    n,f,c=run(f'{root}/s{s}'); res[s]=(n,f,c)
    print(s,n,{k:(f[k],c[k]) for k in sorted(f)})
ids=['81061','81062','81373','82685','82872']
print('detected in seeds:',{i:sum(1 for s in res if i in res[s][1]) for i in ids})
import statistics
for i in ids:
    fs=[res[s][1][i] for s in res if i in res[s][1]]
    if fs: print(i,'first-case index median',statistics.median(fs),'range',min(fs),max(fs),'cases median',statistics.median([res[s][2][i] for s in res if i in res[s][2]]))
