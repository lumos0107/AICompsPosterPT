"""포스터 배경: 양식 디자인 2의 배경 그림에서 오른쪽 위 흰 상자를 지운다 (2026-11-13).

상자는 배경 그림(양식 슬라이드 2의 그림 119)에 박혀 있어 옮길 수 없다. 그래서
- 물결 위(파랑·육각형 무늬): 같은 열의 위쪽 무늬를 세로 주기만큼 내려 복사하고,
- 물결 띠와 흰 바탕: 상자 왼쪽·오른쪽 바로 바깥 열에서 띠 경계(y)를 찾아 그 사이를 직선으로 이어 다시 칠한다.
새 상자는 make_poster.py가 PowerPoint 도형으로 더 위에 그린다.
실행: python make_bg.py → 그림/배경_상자없음.png (확인용 그림은 임시 폴더에)
"""
import io
import os
import sys

import numpy as np
from PIL import Image
from pptx import Presentation

sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(HERE))))
TEMPLATE = os.path.join(ROOT, "3학년_2학기", "AI웅합콜로퀴움", "대회자료", "AI융합콜로퀴움_논문포스터PPT-1.pptx")
OUT = os.path.join(HERE, "그림", "배경_상자없음.png")

prs = Presentation(TEMPLATE)
bg = next(s for s in prs.slides[1].shapes if s.shape_id == 120)
im = np.array(Image.open(io.BytesIO(bg.image.blob)).convert("RGB")).astype(float)
H, W, _ = im.shape
ppi = W / 14.6528

# 상자(테두리·그림자 포함) 영역: 흰색이 아닌 테두리를 기준으로 넉넉히
x0, x1 = int(10.93 * ppi), int(14.14 * ppi)
y0, y1 = int(2.08 * ppi), int(4.05 * ppi)
gray = im.mean(axis=2)


def bands(col):
    """한 열에서 위에서부터 '파랑 → 띠 → 흰색'으로 바뀌는 y와 각 구간 색."""
    c = im[:, col, :]
    lum = c.mean(axis=1)
    # 흰 바탕 시작: 위에서 내려오며 처음으로 밝기 245 이상이 이어지는 곳(머리띠 아래)
    ys = [y for y in range(int(2.0 * ppi), int(4.6 * ppi)) if lum[y] > 245 and lum[min(y + 6, H - 1)] > 245]
    white = ys[0]
    return white


xl, xr = x0 - 12, x1 + 12
wl, wr = bands(xl), bands(xr)
print("흰 바탕 시작 y(인치): 왼쪽", round(wl / ppi, 2), "오른쪽", round(wr / ppi, 2))

# 물결 띠는 흰 바탕 위로 몇 개의 색 구간이 있다. 왼쪽 열 기준으로 띠의 두께(흰 바탕에서 위로 몇 px)를 재고 색을 저장
def band_profile(col, white, depth=90):
    return im[white - depth:white, col, :].copy()


depth = 46  # 물결 띠 두께(px). 더 크면 위쪽 무늬 선까지 복사된다
pl, pr = band_profile(xl, wl, depth), band_profile(xr, wr, depth)
out = im.copy()

# 1) 물결 위: 육각형 무늬를 세로 주기로 복사. 주기는 상자 위 영역의 자기상관으로 찾는다.
ref = gray[int(0.3 * ppi):y0 - 2, x0:x1]
best, period = None, None
for p in range(40, 200):
    a, b = ref[p:], ref[:-p]
    e = float(np.mean((a - b) ** 2))
    if best is None or e < best:
        best, period = e, p
print("무늬 세로 주기(px):", period, "오차", round(best, 2))

for x in range(x0, x1):
    t = (x - xl) / (xr - xl)
    wf = wl + t * (wr - wl)                  # 흰 바탕 시작(소수 px): 띠를 부드럽게 잇기 위해 반올림하지 않는다
    for y in range(y0, y1):
        k = y - (wf - depth)                 # 띠 안에서의 위치(소수)
        if k < 0:
            sy = y
            while sy >= y0 - 2:
                sy -= period
            out[y, x] = im[sy, x]
        elif k < depth - 1:
            k0 = int(k)
            f = k - k0
            cl = (1 - f) * pl[k0] + f * pl[min(k0 + 1, depth - 1)]
            cr = (1 - f) * pr[k0] + f * pr[min(k0 + 1, depth - 1)]
            out[y, x] = (1 - t) * cl + t * cr
        else:
            out[y, x] = (1 - t) * im[y, xl] + t * im[y, xr]   # 흰 바탕도 양옆 실제 색으로

Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).save(OUT)
print("저장:", OUT)
