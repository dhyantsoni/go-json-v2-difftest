import base64, collections, re, sys
cases=[l.rstrip('\n').split('\t') for l in open(sys.argv[1])]
a=[l.rstrip('\n').split('\t',1)[1] for l in open(sys.argv[2])]; b=[l.rstrip('\n').split('\t',1)[1] for l in open(sys.argv[3])]
TN=['User','Event','Config','map[string]any','[]any','map[string]string','[]int','Item']
def fields(d):
    # split a dump "{A:x B:y }" at depth 0 into field strings
    s=d.split(' | ',1)[1]
    if not s.startswith('{'): return {'_':s}
    out={}; depth=0; cur=''; s=s[1:-1]
    for ch in s:
        if ch in '{[(': depth+=1
        if ch in '}])': depth-=1
        if ch==' ' and depth==0:
            if ':' in cur: k,v=cur.split(':',1); out[k]=v
            cur=''
        else: cur+=ch
    return out
C=collections.Counter(); ex={}
for i,(x,y) in enumerate(zip(a,b)):
    if x==y: continue
    c=cases[i]; t=TN[int(c[1])]; mode=c[2]
    ea,eb=x.split(' | ')[0],y.split(' | ')[0]
    inp=base64.b64decode(c[3]).decode('utf-8','replace') if mode!='marshal' else ''
    if mode=='marshal':
        if '\\ufffd' in x and '�' in y: k='#82685 U+FFFD literal'
        else: k=f'marshal other {ea}->{eb}'
    elif 'Inf' in y and 'Inf' not in x: k='#81062 +-Inf left in destination'
    else:
        fa,fb=fields(x),fields(y)
        diff=sorted(f for f in set(fa)|set(fb) if fa.get(f)!=fb.get(f))
        if not diff: k=f'error type only {ea}->{eb}'
        else: k=f'{t} {mode} value diff in {diff[:3]} err {ea!="ok"}/{eb!="ok"}'
    C[k]+=1; ex.setdefault(k,(i,inp[:110],x[:150],y[:150]))
for k,n in C.most_common(): print(n,k)

