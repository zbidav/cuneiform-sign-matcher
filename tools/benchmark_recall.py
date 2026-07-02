import json, math, random, numpy as np
random.seed(7)
d=json.loads(open('docs/js/signs-data.js').read()[len('window.SIGNS='):-2])
def cloud(polys, step=0.04):
    pts=[p for pl in polys for p in pl]; xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
    mnx,mxx,mny,mxy=min(xs),max(xs),min(ys),max(ys); w,h=mxx-mnx,mxy-mny
    sc=1/(max(w,h) or 1); ox=(1-w*sc)/2; oy=(1-h*sc)/2; out=[]
    for pl in polys:
        t=[[(x-mnx)*sc+ox,(y-mny)*sc+oy] for x,y in pl]
        for j in range(len(t)-1):
            x1,y1=t[j]; x2,y2=t[j+1]; L=math.hypot(x2-x1,y2-y1); n=max(1,round(L/step))
            for k in range(n): u=k/n; out.append([x1+(x2-x1)*u,y1+(y2-y1)*u])
        if t: out.append(t[-1])
    return np.array(out)
def cham(A,B):
    D=np.sqrt(((A[:,None]-B[None])**2).sum(-1)); return D.min(1).mean()+D.min(0).mean()
# reference set = Noto (all 879), flipped
REF=[]
for s in d:
    fl=[[[x,-y] for x,y in pl] for pl in s['g']]
    REF.append((s['cp'], cloud(fl)))
cps=[r[0] for r in REF]; clouds=[r[1] for r in REF]
def perturb(polys, ang, jit):
    ca,sa=math.cos(ang),math.sin(ang); out=[]
    for pl in polys:
        np2=[]
        for x,y in pl:
            rx,ry=x*ca-y*sa,x*sa+y*ca
            np2.append([rx+random.gauss(0,jit),ry+random.gauss(0,jit)])
        out.append(np2)
    return out
sample=random.sample(range(len(d)), 150)
def run(ang_deg, jit_frac):
    r1=r5=r10=r24=0
    for si in sample:
        s=d[si]; fl=[[[x,-y] for x,y in pl] for pl in s['g']]
        # jitter scaled to glyph size
        pts=[p for pl in fl for p in pl]; xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        size=max(max(xs)-min(xs), max(ys)-min(ys)) or 1
        q=cloud(perturb(fl, math.radians(random.uniform(-ang_deg,ang_deg)), jit_frac*size))
        ds=np.array([cham(q,c) for c in clouds]); order=np.argsort(ds)
        rank=list(order).index(si)
        r1+=rank<1; r5+=rank<5; r10+=rank<10; r24+=rank<24
    n=len(sample)
    print(f"  rot=±{ang_deg}deg jitter={jit_frac:.0%}: recall@1={r1/n:.0%} @5={r5/n:.0%} @10={r10/n:.0%} @24={r24/n:.0%}")
print(f"Recall over {len(sample)} random signs (search space = 879 Noto forms):")
run(4, 0.01)    # near-perfect trace
run(8, 0.03)    # rough hand copy
run(12, 0.05)   # sloppy sketch
