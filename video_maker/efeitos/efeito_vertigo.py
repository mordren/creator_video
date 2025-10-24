# efeitos/efeito_vertigo.py
import os, cv2, numpy as np
from pathlib import Path

def criar_video_vertigo_depth(img_path, temp=3, depth_path=None, fps=60, focus_x=0.5, focus_y=0.5):
    Path('./renders/temp/').mkdir(parents=True, exist_ok=True)
    nome_base = os.path.splitext(os.path.basename(img_path))[0]
    saida = os.path.join('./renders/temp/', f"{nome_base}_vertigo.mp4")

    img = cv2.imread(img_path)
    h, w, _ = img.shape

    depth = cv2.imread(depth_path, 0).astype(np.float32) / 255.0
    depth = cv2.resize(depth, (w, h))
    # suavização robusta (menos “vidro quebrado”)
    depth = cv2.bilateralFilter(depth, d=9, sigmaColor=0.15, sigmaSpace=7)
    depth = cv2.GaussianBlur(depth, (9, 9), 0)

    cx, cy = w * focus_x, h * focus_y
    focus_d = float(depth[int(np.clip(cy, 0, h-1)), int(np.clip(cx, 0, w-1))])

    n = int(temp * fps)
    out = cv2.VideoWriter(saida, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    yy, xx = np.indices((h, w), dtype=np.float32)

    # parâmetros conservadores
    dolly_max     = 12.0   # intensidade de parallax total
    zoom_out_max  = 0.06   # quanto “abre” no final
    r_protec      = 0.16   # raio de proteção ao redor do foco
    cap_rel       = 0.012  # limite máx. de deslocamento relativo (1.2% da dimensão)
    parallax_gain = 0.85   # ganho geral do parallax

    # máscaras: queda radial + supressão em bordas (gradiente do depth)
    dxn = (xx - cx) / w
    dyn = (yy - cy) / h
    radial = np.sqrt(dxn*dxn + dyn*dyn)
    falloff = np.clip((radial - r_protec) / (1.0 - r_protec), 0.0, 1.0) ** 1.7

    gx = cv2.Sobel(depth, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(depth, cv2.CV_32F, 0, 1, ksize=3)
    gmag = cv2.magnitude(gx, gy)
    gmag = gmag / (gmag.max() + 1e-6)
    edge_suppress = np.exp(-6.0 * gmag)  # 1 em áreas lisas, ~0 em arestas

    mask = falloff * edge_suppress

    base = np.clip((depth - focus_d), -0.15, 0.15) * parallax_gain

    for i in range(n):
        t = i / max(1, n-1)
        ease = t*t*(3 - 2*t)  # smoothstep

        dolly = dolly_max * ease
        zoom  = 1.0 - zoom_out_max * ease

        shift_scale = dolly * base * mask
        shift_x = np.clip(dxn * shift_scale * w, -cap_rel*w, cap_rel*w)
        shift_y = np.clip(dyn * shift_scale * h, -cap_rel*h, cap_rel*h)

        map_x = xx + shift_x
        map_y = yy + shift_y

        map_x = (map_x - cx) / zoom + cx
        map_y = (map_y - cy) / zoom + cy

        warped = cv2.remap(
            img,
            map_x.astype(np.float32),
            map_y.astype(np.float32),
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT_101
        )
        # leve mistura com o original para “amarrar” microartefatos
        blended = cv2.addWeighted(warped, 0.92, img, 0.08, 0.0)
        out.write(blended)

    out.release()
    class Sucesso: filename = saida
    return Sucesso()
