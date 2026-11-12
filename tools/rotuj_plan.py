import sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
exec(open(__file__.replace('rotuj_plan.py','rotuj_plan_prep.py')).read().split('bm=')[0])
THETA=float(sys.argv[1]) if len(sys.argv)>1 else 45.0
OUT=sys.argv[2] if len(sys.argv)>2 else 'v45'
K=0.75; HW=32
shc=np.isin(R*65536+G*256+B,[124*65536+100*256+80,120*65536+88*256+76,116*65536+76*256+68])
shadow=cv2.morphologyEx(shc.astype(np.uint8),cv2.MORPH_OPEN,np.ones((5,5),np.uint8))>0
nonfloor=~(floor|shadow)
nf=cv2.morphologyEx(nonfloor.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((3,3),np.uint8))
nf=cv2.morphologyEx(nf,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
lab,n=ndi.label(nf)
sz=ndi.sum(nf,lab,range(1,n+1)); wid=1+int(np.argmax(sz))
S=lab==wid
# nieregularne rogi: wypelnij male dziury w scianach (<400 px)
holes=ndi.binary_fill_holes(S)&~S
hl,hn=ndi.label(holes); hs=ndi.sum(holes,hl,range(1,hn+1))
for i,s in enumerate(hs):
    if s<400: S|=hl==i+1
shifted=np.zeros_like(S); shifted[HW:]=S[:H-HW]; shifted[:HW]=S[0]   # gora krawedzi: powielony wiersz (bez szczeliny)
Fp=S&shifted                      # slad sciany na gruncie
props=[]; decal=np.zeros((H,W),bool)
for i in range(1,n+1):
    if i==wid: continue
    m=lab==i; area=sz[i-1]
    if area<25: continue
    ys,xs=np.where(m)
    if area>20000: decal|=m; continue
    props.append((xs.min(),ys.min(),xs.max()+1,ys.max()+1,m))
print('props',len(props),'decal',decal.sum(),'S',S.mean(),'Fp',Fp.mean())
# tekstury
def best_window(mask,sz_):
    ii=cv2.integral(mask.astype(np.uint8)); h,w=mask.shape
    s=ii[sz_:,sz_:]-ii[:-sz_,sz_:]-ii[sz_:,:-sz_]+ii[:-sz_,:-sz_]
    j=int(np.argmax(s)); y,x=divmod(j,s.shape[1]); print('okno',s.max()/(sz_*sz_)); return y,x
fy,fx=best_window(floor,96); FLOOR=im[fy:fy+96,fx:fx+96]
brickfull=brick&~props_mask if False else None
bm7=cv2.morphologyEx(brick.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((5,5),np.uint8))>0
inner=cv2.erode((S&shifted).astype(np.uint8),np.ones((121,121),np.uint8))>0
ys_,xs_=np.where(inner); j=len(ys_)//2; by,bx=ys_[j]-48,xs_[j]-48; BRICK=im[by+16:by+80,bx+16:bx+80]
print('S col800',np.where(S[150:260,800])[0]+150)
print('okna',fy,fx,by,bx)
# pas sciany (kamien): kolumny x 420..1200 przy dlugiej scianie, wiersze od dolu cegly
FACE=None
col=S[:,800]; ys=np.where(col[150:260])[0]+150
ye=ys.max(); FACE=im[176:208,420:1200]
Image.fromarray(np.concatenate([np.pad(FLOOR,((0,0),(0,0),(0,0))),np.zeros((96,10,3),np.uint8),np.pad(BRICK,((0,32),(0,32),(0,0)))],1)).save(OUT+'_tex.png')
# transformacja
th=np.deg2rad(THETA); c,s_=np.cos(th),np.sin(th)
cx,cy=W/2,H/(2*K)
hw,hh=W/2,H/(2*K)
ext_x=abs(hw*c)+abs(hh*s_); ext_y=abs(hw*s_)+abs(hh*c)
W2=int(2*ext_x)+40; H2=int(2*ext_y*K)+40+HW
cx2,cy2=W2/2,(H2+HW)/2
yy,xx=np.mgrid[0:H2,0:W2].astype(np.float32)
px=(xx-cx2); py=(yy-cy2)/K
Px=c*px+s_*py+cx; Py=-s_*px+c*py+cy       # plan oryginalu
ox=Px.astype(np.float32); oy=(Py*K).astype(np.float32)
inrect=(ox>=0)&(ox<W-1)&(oy>=0)&(oy<H-1)
def samp(a,interp=cv2.INTER_LINEAR): return cv2.remap(a,ox,oy,interp,borderMode=cv2.BORDER_REPLICATE)
Fn=(samp(Fp.astype(np.float32))>0.5)
Fn=cv2.medianBlur((Fn*255).astype(np.uint8),13)>127
Fn=Fn|~inrect
# podloga: tekstura w plan-coords
fx_=(Px%96).astype(int); fy_=(Py%96).astype(int)
ground=FLOOR[fy_%96,fx_%96].copy()
# kafle ground-decal (basen) z oryginalu
dm=samp(decal.astype(np.float32))>0.5
rgb=cv2.remap(im,ox,oy,cv2.INTER_LINEAR,borderMode=cv2.BORDER_REPLICATE)
ground[dm]=rgb[dm]
# cien: rzut sciany wektorem (dx,dy)
sh=np.zeros_like(Fn)
for t in np.linspace(0,1,12):
    dx,dy=int(22*t),int(24*t)
    M=np.float32([[1,0,dx],[0,1,dy]]); sh|=cv2.warpAffine(Fn.astype(np.uint8),M,(W2,H2))>0
sh&=~Fn
ground=ground.astype(np.float32); ground[sh]*=np.array([0.80,0.64,0.68],np.float32)
ground=ground.clip(0,255).astype(np.uint8)
# sciany: kolumnowo
wall=np.zeros((H2,W2,3),np.uint8); key=np.full((H2,W2),-1,np.int32); has=np.zeros((H2,W2),bool)
brickg=BRICK[(Py.astype(int))%64,(Px.astype(int))%64]
# jak w wnetrzach BG1 (np. AR2615, AR0516, AR2610): przy podlodze cienki pas muru, glebiej czern
DEPTH=int(sys.argv[3]) if len(sys.argv)>3 else 40
dist=cv2.distanceTransform(Fn.astype(np.uint8),cv2.DIST_L2,5)
brickg[dist>DEPTH]=0
fh=FACE.shape[0]; fw=FACE.shape[1]
for x in range(W2):
    colv=Fn[:,x].astype(np.int8); d=np.diff(np.concatenate([[0],colv,[0]]))
    st=np.where(d==1)[0]; en=np.where(d==-1)[0]-1
    for a_,e_ in zip(st,en):
        t0=max(a_-HW,0); t1=e_-HW            # wiersze gory (ekran)
        if t1>=t0:
            ys_=np.arange(t0,t1+1); wall[ys_,x]=brickg[ys_+HW,x]; key[ys_,x]=np.maximum(key[ys_,x],e_); has[ys_,x]=True
        if e_>=H2-1: continue            # krawedz kadru: bez pasa sciany (czern)
        f0=max(e_-HW+1,0); ys_=np.arange(f0,e_+1)
        v=np.clip(ys_-(e_-HW+1),0,fh-1)
        wall[ys_,x]=FACE[v,x%fw]; key[ys_,x]=np.maximum(key[ys_,x],e_); has[ys_,x]=True
canvas=ground.copy()
# sprite'y
spr=np.zeros((H2,W2,3),np.uint8); sa=np.zeros((H2,W2),bool); sk=np.full((H2,W2),-1,np.int32)
placed=0; prects=[]
for (x0,y0,x1,y1,m) in sorted(props,key=lambda t:t[3]):
    gx,gy=(x0+x1)/2,y1-1
    Pgx,Pgy=gx,gy/K
    qx,qy=Pgx-cx,Pgy-cy
    nx=c*qx-s_*qy+cx2; ny=K*(s_*qx+c*qy)+cy2
    nx=int(round(nx)); ny=int(round(ny))
    bw,bh=x1-x0,y1-y0
    X0=nx-bw//2; Y0=ny-bh+1
    if X0<0 or Y0<0 or X0+bw>W2 or Y0+bh>H2: continue
    if Fn[min(ny,H2-1),nx]: continue
    mm=m[y0:y1,x0:x1]
    reg=spr[Y0:Y0+bh,X0:X0+bw]; reg[mm]=im[y0:y1,x0:x1][mm]
    sa[Y0:Y0+bh,X0:X0+bw]|=mm
    k2=sk[Y0:Y0+bh,X0:X0+bw]; k2[mm]=ny; placed+=1; prects.append((X0,Y0,bw,bh,ny))
print('sprite',placed)
out=canvas.copy()
w_=has&~(sa&(sk>key)); out[w_]=wall[w_]
s_only=sa&~(has&(key>=sk)); out[s_only]=spr[s_only]
Image.fromarray(out).save(OUT+'.png')
Image.fromarray(out).resize((W2//2,H2//2),Image.LANCZOS).save(OUT+'_small.png')
np.save(OUT+'_Fn.npy',Fn); np.save(OUT+'_dm.npy',dm); np.save(OUT+'_spr.npy',np.array(prects))
print(W2,H2)
