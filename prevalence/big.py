import json,urllib.request,time,subprocess,os,re,shutil,concurrent.futures as cf,collections
items=[]
for page in range(1,6):
    u=f"https://api.github.com/search/repositories?q=language:go+stars:>2000+size:<60000+archived:false&sort=stars&order=desc&per_page=100&page={page}"
    for _ in range(3):
        try: items+=json.load(urllib.request.urlopen(u,timeout=30)).get('items',[]); break
        except Exception: time.sleep(10)
    time.sleep(3)
print('repos',len(items),flush=True)
env=dict(os.environ,GOTOOLCHAIN='go1.27.4',GOMODCACHE=os.path.abspath('modcache'),GOFLAGS='-mod=mod',GOPROXY='https://proxy.golang.org')
keys=['MapKeyWithUnmarshalJSON','NumberWithString','TextTypeWithString','StringOption','TimeFieldJSON','MethodFieldJSON','FloatKeyMap','IfaceEmbedsMarshaler','ImportsJSON']
def one(r):
    full,br=r['full_name'],r['default_branch']
    try:
        t=urllib.request.urlopen(f"https://raw.githubusercontent.com/{full}/{br}/go.mod",timeout=20).read().decode()
        mod=re.search(r'^module\s+(\S+)',t,re.M).group(1).strip('"')
    except Exception: return full,None,'no go.mod'
    p=subprocess.run(['go','mod','download','-json',mod+'@latest'],capture_output=True,text=True,env=env,timeout=600)
    try: d=json.loads(p.stdout)['Dir']
    except Exception: return full,None,'proxy'
    c=json.loads(subprocess.run(['./scan',d],capture_output=True,text=True,timeout=600).stdout)
    shutil.rmtree(d,ignore_errors=True)
    return full,c,mod
res=[]
with cf.ThreadPoolExecutor(4) as ex:
    for k,r in enumerate(ex.map(one,items)):
        res.append(r)
        if k%50==0: print(k,flush=True)
json.dump(res,open('big.json','w'))
ok=[(f,c) for f,c,m in res if c and c.get('ImportsJSON')]
print('scanned',sum(1 for _,c,_ in res if c),'importing encoding/json',len(ok))
for k in keys[:-1]:
    n=sum(1 for f,c in ok if c[k]); occ=sum(c[k] for f,c in ok)
    print(f'{k:26s} {n:4d}/{len(ok)} ({n/len(ok):5.1%}) occ {occ:6d} e.g. {[f for f,c in ok if c[k]][:4]}')
