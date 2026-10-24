"""Real, reproducible knowledge-distillation demo on MNIST (MLX, Apple Silicon).
Teacher: 784-1200-1200-10 MLP with dropout. Student: 784-32-10 MLP.
Experiments (each student run with 3 seeds):
  A  student from hard labels, small transfer set (2,000 examples)
  B  student from teacher soft targets at T=4 (same 2,000 examples, labels unused)
  C  "mythical 3": transfer set with every 3 removed; hard-label vs distilled student, measured on test 3s
     (distilled student's 3-bias adjusted using its own held-out training data, per Hinton et al. 2015 §3)
Outputs results.json + soft-target example. Nothing here is illustrative; all numbers are measured."""
from pathlib import Path
import gzip,json,time,hashlib,datetime,platform
import numpy as np, mlx.core as mx, mlx.nn as nn, mlx.optimizers as optim
D=Path(__file__).resolve().parent
def load(n):
    raw=gzip.open(D/'data'/n).read()
    return np.frombuffer(raw,np.uint8,offset=16).reshape(-1,784).astype(np.float32)/255. if 'images' in n else np.frombuffer(raw,np.uint8,offset=8).astype(np.int32)
Xtr,ytr,Xte,yte=load('train-images-idx3-ubyte.gz'),load('train-labels-idx1-ubyte.gz'),load('t10k-images-idx3-ubyte.gz'),load('t10k-labels-idx1-ubyte.gz')
class MLP(nn.Module):
    def __init__(s,dims,drop=0.0):
        super().__init__();s.layers=[nn.Linear(a,b) for a,b in zip(dims[:-1],dims[1:])];s.drop=nn.Dropout(drop) if drop else None
    def __call__(s,x):
        for l in s.layers[:-1]:
            x=nn.relu(l(x))
            if s.drop is not None:x=s.drop(x)
        return s.layers[-1](x)
def acc(m,X,y):
    was=m.training;m.eval();p=np.array(mx.argmax(m(mx.array(X)),axis=1));m.train(was);return float((p==y).mean())
def train(m,X,targets,epochs,lr,bs,loss_kind,T=1.0,seed=0):
    rng=np.random.default_rng(seed);opt=optim.Adam(learning_rate=lr)
    def lossf(m,x,t):
        z=m(x)
        if loss_kind=='hard':return nn.losses.cross_entropy(z,t,reduction='mean')
        return -(t*nn.log_softmax(z/T,axis=1)).sum(axis=1).mean()*T*T
    g=nn.value_and_grad(m,lossf)
    for e in range(epochs):
        idx=rng.permutation(len(X))
        for i in range(0,len(X),bs):
            b=idx[i:i+bs];l,gr=g(m,mx.array(X[b]),mx.array(targets[b]));opt.update(m,gr);mx.eval(m.parameters(),opt.state)
    return m
out={'started':datetime.datetime.now().astimezone().isoformat(),'host':platform.platform(),'mlx':mx.__version__ if hasattr(mx,'__version__') else 'unknown',
     'data_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((D/'data').glob('*.gz'))}}
# Teacher on full 60k
mx.random.seed(0);t0=time.time()
teacher=MLP([784,1200,1200,10],drop=0.2);train(teacher,Xtr,ytr,epochs=8,lr=1e-3,bs=128,loss_kind='hard',seed=0)
teacher.eval();out['teacher']={'arch':'784-1200-1200-10 ReLU, dropout 0.2','params':int(sum(v.size for _,v in nn.utils.tree_flatten(teacher.parameters()))),'test_acc':acc(teacher,Xte,yte),'train_seconds':time.time()-t0}
T=4.0
def soft(X):
    teacher.eval();assert not teacher.training
    return np.array(mx.softmax(teacher(mx.array(X))/T,axis=1))
# Soft target example: a test image of a 2 whose runner-up is interesting
teacher.eval();assert not teacher.training
probsT1=np.array(mx.softmax(teacher(mx.array(Xte)),axis=1));probsT=np.array(mx.softmax(teacher(mx.array(Xte))/T,axis=1))
cand=[i for i in range(len(yte)) if yte[i]==2 and probsT1[i].argmax()==2]
ex=max(cand,key=lambda i:np.sort(probsT[i])[-2])
out['soft_example']={'test_index':int(ex),'label':2,'T1':probsT1[ex].round(5).tolist(),'T4':probsT[ex].round(4).tolist(),'image':Xte[ex].reshape(28,28).round(3).tolist()}
rng=np.random.default_rng(1);sub=rng.choice(len(Xtr),2000,replace=False);Xs,ys=Xtr[sub],ytr[sub]
S=[784,32,10];res={'A_hard_2000':[],'B_soft_2000':[]}
for seed in range(3):
    mx.random.seed(100+seed);a=MLP(S);train(a,Xs,ys,40,2e-3,64,'hard',seed=seed);res['A_hard_2000'].append(acc(a,Xte,yte))
    mx.random.seed(100+seed);b=MLP(S);train(b,Xs,soft(Xs),40,2e-3,64,'soft',T=T,seed=seed);res['B_soft_2000'].append(acc(b,Xte,yte))
out['student']={'arch':'784-32-10 ReLU','params':int(sum(v.size for _,v in nn.utils.tree_flatten(MLP(S).parameters()))),'transfer_examples':2000,'epochs':40,'T':T,'runs':res,
 'mean':{k:float(np.mean(v)) for k,v in res.items()}}
# Mythical 3 (transfer set = 10,000 random training examples minus all 3s)
sub2=np.random.default_rng(2).choice(len(Xtr),10000,replace=False);keep=sub2[ytr[sub2]!=3];X3,y3=Xtr[keep],ytr[keep]
hold=np.random.default_rng(3).choice(np.setdiff1d(np.arange(len(Xtr)),sub2),5000,replace=False)  # for bias calibration only
m3={'hard':[],'distilled_raw':[],'distilled_bias':[],'bias':[]}
is3=yte==3
for seed in range(3):
    mx.random.seed(200+seed);h=MLP(S);train(h,X3,y3,30,2e-3,64,'hard',seed=seed);h.eval();p=np.array(mx.argmax(h(mx.array(Xte)),axis=1));m3['hard'].append(float((p[is3]==3).mean()))
    mx.random.seed(200+seed);d=MLP(S);train(d,X3,soft(X3),30,2e-3,64,'soft',T=T,seed=seed);d.eval();z=np.array(d(mx.array(Xte)))
    m3['distilled_raw'].append(float((z.argmax(1)[is3]==3).mean()))
    zh=np.array(d(mx.array(Xtr[hold])));yh=ytr[hold];best=(0,-1)
    for bb in np.arange(0,8.01,0.25):
        zz=zh.copy();zz[:,3]+=bb;a_=float((zz.argmax(1)==yh).mean());best=max(best,(a_,bb))
    zz=z.copy();zz[:,3]+=best[1];m3['bias'].append(float(best[1]));m3['distilled_bias'].append(float((zz.argmax(1)[is3]==3).mean()))
out['mythical3']={'transfer_examples':int(len(X3)),'threes_in_transfer':0,'test_threes':int(is3.sum()),'runs':m3,'mean':{k:float(np.mean(v)) for k,v in m3.items()},
 'bias_method':'single additive logit bias for class 3 chosen to maximize accuracy on 5,000 held-out training images (all classes); test set untouched'}
out['finished']=datetime.datetime.now().astimezone().isoformat()
(D/'results.json').write_text(json.dumps(out,indent=1));print(json.dumps({k:v for k,v in out.items() if k not in('soft_example',)},indent=1)[:3000]);print('soft T1',out['soft_example']['T1']);print('soft T4',out['soft_example']['T4'])
