import numpy as np, cv2
from PIL import Image
from scipy import ndimage as ndi
SRC='/mnt/user-data/attachments/01e382cf-65b3-5716-b9cd-71f1296da638/a9a05436-image.png'
im=np.asarray(Image.open(SRC).convert('RGB')); H,W,_=im.shape
a=im.astype(int); R,G,B=a[...,0],a[...,1],a[...,2]
floor=(R-G>=-2)&(R-G<=18)&(G-B>=22)&(R>=128)
shadow=(R-G>=20)&(R-G<=46)&(G-B>=4)&(G-B<=26)&(R>=100)&(R<=135)
rock=(G-B>=40)&(R-G>=20)
brick=(R-G>=30)&(G-B<35)&~shadow&~rock
bm=cv2.morphologyEx(brick.astype(np.uint8),cv2.MORPH_CLOSE,np.ones((7,7),np.uint8))
lab,n=ndi.label(bm)
sz=ndi.sum(bm,lab,range(1,n+1))
big=np.isin(lab,[i+1 for i,s in enumerate(sz) if s>20000])
TOP=big&(brick|((~floor)&(~shadow)&(~rock)))   # cegla + ciemna fuga
np.save('/tmp/TOP.npy',TOP)
print(n,sorted(sz)[-5:],TOP.mean())
Image.fromarray((np.stack([TOP,floor|shadow,rock],-1)*255).astype(np.uint8)).resize((1024,784)).save('/tmp/cls.png')
