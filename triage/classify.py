import re,base64,collections,sys,json
d=sys.argv[1]
types={}
for m in re.finditer(r'type T(\d+) struct \{\n\tF (\S+)(?: `json:"([^"]*)"`)?\n\}', open(f'{d}/types.go').read()):
    types[int(m.group(1))]=(m.group(2), m.group(3))
cases=[l.rstrip('\n').split('\t') for l in open(f'{d}/cases.tsv')]
a=[l.rstrip('\n').split('\t',1)[1] for l in open(f'{d}/v1.out')]; b=[l.rstrip('\n').split('\t',1)[1] for l in open(f'{d}/v2.out')]
def known(k,t,mode,x,y,inp):
    ea,eb=x.split(' | ')[0],y.split(' | ')[0]; va,vb=x.split(' | ',1)[-1],y.split(' | ',1)[-1]
    opts=(t or '').split(',')[1:]
    if mode=='marshal' and '\\ufffd' in x and '�' in y: return '#82685 U+FFFD'
    if 'map[float64]' in k and mode!='marshal' and '"null"' not in inp: return '#81373 float keys'
    if mode!='marshal' and ('map[float64]' in k or 'map[int' in k or 'map[uint' in k) and '"null"' in inp: return '#82872 null numeric key'
    if k in ('map[KeyJ]int','map[KeyJT]int') and mode!='marshal': return '#83391 key UnmarshalJSON'
    if k=='json.Number' and 'string' in opts and mode!='marshal': return '#83392 Number ,string'
    if k=='time.Time' and mode=='prefill' and ea!='ok' and eb!='ok': return '#83393 time keeps value'
    if k=='IM' and 'PANIC' in y: return '#82682 iface Marshaler panic'
    if ea!='ok' and eb!='ok' and va==vb: return 'error type only'
    if ea!='ok' and eb=='ok' and mode=='marshal' and va=='': return 'marshal: v1 error, v2 ok (unsupported type?)'
    return None
C=collections.Counter(); ex={}
for i,c in enumerate(cases):
    if a[i]==b[i]: continue
    k,t=types[int(c[1])]; mode=c[2]
    inp=base64.b64decode(c[3]).decode('utf-8','replace') if mode!='marshal' else ''
    cls=known(k,t,mode,a[i],b[i],inp) or 'UNTRIAGED'
    key=(cls,k,t,mode); C[key]+=1; ex.setdefault(key,(inp[:90],a[i][:120],b[i][:120]))
agg=collections.Counter(); 
for (cls,k,t,m),n in C.items(): agg[cls]+=n
for cls,n in agg.most_common(): print(f'{n:6d} {cls}')
print('\nUNTRIAGED groups (kind, tag, mode):')
for (cls,k,t,m),n in sorted(C.items(),key=lambda x:-x[1]):
    if cls in('UNTRIAGED','marshal: v1 error, v2 ok (unsupported type?)'):
        e=ex[(cls,k,t,m)]; print(f'{n:4d} {cls[:12]} {k} tag={t!r} {m}\n      in: {e[0]}\n      v1: {e[1]}\n      v2: {e[2]}')
