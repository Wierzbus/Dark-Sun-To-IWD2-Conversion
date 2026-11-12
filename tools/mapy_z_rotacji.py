"""Wyniki tools/rotuj_plan.py (NAZWA.png, _Fn/_dm/_spr.npy) -> areas_custom/ARxxxx: obraz.png, SR/HT/LM.BMP, sciany.png.
Uzycie: python tools/mapy_z_rotacji.py PREFIX KATALOG_WYJ --bg-dir "D:\\Gry\\Baldurs Gate"
SR: slad scian (Fn) = 0 (sciana), basen i podstawy mebli = 8 (niska przeszkoda), reszta 1; HT plaskie 7; LM biale (paleta z BG1 AR2600).
sciany.png: sylwetka murow (slad przesuniety w gore o wysokosc sciany) - z niej powstaja wielokaty scian WED."""
import sys, os, argparse, numpy as np, cv2
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from PIL import Image
from geometry import maps as M
from inventory.resource_reader import GameResources
ap = argparse.ArgumentParser(); ap.add_argument('prefix'); ap.add_argument('out'); ap.add_argument('--bg-dir', required=True)
ap.add_argument('--wall-h', type=int, default=32)
o = ap.parse_args()
img = Image.open(o.prefix + '.png').convert('RGB'); W, H = img.size
Fn = np.load(o.prefix + '_Fn.npy'); dm = np.load(o.prefix + '_dm.npy'); spr = np.load(o.prefix + '_spr.npy')
tw, th = -(-W // 64), -(-H // 64); PW, PH = tw * 64, th * 64
CW, CH = 16, 12
def pad(m): return np.pad(m, ((0, PH - m.shape[0]), (0, PW - m.shape[1])), constant_values=True)
blocked = pad(Fn)
obst = np.zeros((PH, PW), bool)
obst[:H, :W] |= dm
for X0, Y0, bw, bh, ny in spr:
    obst[max(ny - 10, 0):ny + 1, max(X0, 0):X0 + bw] = True
def cells(m): return m.reshape(PH // CH, CH, PW // CW, CW).mean(axis=(1, 3))
SR = np.where(cells(blocked) > 0.4, 0, np.where(cells(obst) > 0.3, 8, 1)).astype(np.uint8)
bg = GameResources(o.bg_dir, 'classic')
psr = M.read_bmp(bg.read('AR2600SR', 'BMP'), name='sr').palette
pht = M.read_bmp(bg.read('AR2600HT', 'BMP'), name='ht').palette
lm = M.read_bmp(bg.read('AR2600LM', 'BMP'), name='lm'); white = lm.palette.index((255, 255, 255))
h, w = SR.shape
os.makedirs(o.out, exist_ok=True)
open(os.path.join(o.out, 'SR.BMP'), 'wb').write(M.write_bmp(M.Bmp(w, h, 4, psr, bytes(SR.flatten()))))
open(os.path.join(o.out, 'HT.BMP'), 'wb').write(M.write_bmp(M.Bmp(w, h, 4, pht, bytes([7]) * (w * h))))
open(os.path.join(o.out, 'LM.BMP'), 'wb').write(M.write_bmp(M.Bmp(w, h, 8, lm.palette, bytes([white]) * (w * h))))
img.save(os.path.join(o.out, 'obraz.png'))
sil = np.zeros_like(blocked)
for d in range(0, o.wall_h + 1):
    sil[:PH - d] |= blocked[d:]
Image.fromarray((sil * 255).astype(np.uint8)).save(os.path.join(o.out, 'sciany.png'))
print('SR', SR.shape, {int(k): int(v) for k, v in zip(*np.unique(SR, return_counts=True))})
