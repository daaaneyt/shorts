"""Cut Adam out of the three race photos -> assets/adam{1,2,3}.png (RGBA).

Needs: pip install rembg onnxruntime opencv-python-headless pillow numpy
(rembg downloads the isnet-general-use and SAM models on first run.)

isnet gives a clean high-res matte, but it keeps every runner in shot. Photo 2
is limited to a SAM mask prompted on Adam (plus two hand-drawn patches for the
runner's leg and shoe behind him), photo 3 to a hand-drawn polygon around Adam.
"""
import numpy as np, cv2
from PIL import Image
from rembg import remove, new_session

A = "assets/"


def fill_holes(m):
    ff = m.copy()
    cv2.floodFill(ff, np.zeros((m.shape[0] + 2, m.shape[1] + 2), np.uint8), (0, 0), 255)
    return m | cv2.bitwise_not(ff)


def poly(shape, pts, offset=(0, 0)):
    m = np.zeros(shape, np.uint8)
    cv2.fillPoly(m, [np.int32([(x + offset[0], y + offset[1]) for x, y in pts])], 255, cv2.LINE_AA)
    return m.astype(np.float32) / 255


isnet = new_session("isnet-general-use")
sam = new_session("sam")
for i in (1, 2, 3):
    im = Image.open(f"{A}photo{i}.webp").convert("RGB")
    rgb = np.asarray(im)
    a = np.asarray(remove(im, session=isnet))[..., 3].astype(np.float32) / 255

    if i == 2:
        pts = [((640, 200), 1), ((520, 700), 1), ((700, 1000), 1), ((560, 1500), 1), ((1100, 1450), 1),
               ((1080, 600), 0), ((1150, 300), 0), ((1100, 1700), 0)]
        s = np.asarray(remove(im, session=sam, sam_prompt=[
            {"type": "point", "data": list(p), "label": l} for p, l in pts]))[..., 3]
        s = (s > 128).astype(np.uint8) * 255
        s = cv2.morphologyEx(s, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (31, 31)))
        s = cv2.dilate(fill_holes(s), cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21)))
        a *= cv2.GaussianBlur(s, (0, 0), 4).astype(np.float32) / 255
        # the runner's leg and shoe that sit between Adam's hand and his back foot
        cut = np.maximum(
            poly(a.shape, [(935, 1150), (1000, 1145), (1040, 1125), (1194, 1125), (1194, 1390), (1140, 1350),
                           (1080, 1335), (1040, 1338), (1015, 1395), (960, 1405), (935, 1380)]),
            poly(a.shape, [(990, 1610), (1030, 1560), (1140, 1635), (1194, 1640), (1194, 1794), (990, 1794)]))
        a *= 1 - cv2.GaussianBlur(cut, (0, 0), 2)

    if i == 3:
        keep = poly(a.shape, [
            (215, 85), (300, 78), (388, 110), (398, 200), (365, 245), (452, 288), (498, 345), (505, 430),
            (470, 470), (448, 540), (446, 620), (420, 665), (402, 710), (396, 800), (406, 900), (442, 955),
            (460, 1050), (452, 1150), (378, 1152), (330, 1020), (300, 1000), (272, 1150), (268, 1272),
            (148, 1268), (148, 1195), (208, 1140), (214, 1000), (244, 905), (240, 790), (192, 690),
            (180, 600), (156, 528), (72, 492), (66, 440), (95, 330), (140, 258), (222, 236)], (120, 220))
        a *= cv2.GaussianBlur(keep, (0, 0), 1.5)

    Image.fromarray(np.dstack([rgb, np.uint8(np.clip(a, 0, 1) * 255)])).save(f"{A}adam{i}.png")
    print("wrote", f"{A}adam{i}.png")
