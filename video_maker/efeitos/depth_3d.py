# efeitos/depth_3d.py
import os, torch, cv2, numpy as np
from pathlib import Path
from PIL import Image
from transformers import DPTImageProcessor, DPTForDepthEstimation


def carregar_modelo_local():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    base_dir = Path("./models/models--Intel--dpt-hybrid-midas")

    # tenta localizar o snapshot local
    snapshot_dir = base_dir / "snapshots"
    if snapshot_dir.exists():
        snapshots = list(snapshot_dir.glob("*"))
        if snapshots:
            model_dir = snapshots[0]
            print(f"✅ Usando modelo local ({model_dir.name}).")
            processor = DPTImageProcessor.from_pretrained(str(model_dir), local_files_only=True)
            model = DPTForDepthEstimation.from_pretrained(str(model_dir), local_files_only=True).to(device)
            model.eval()
            return processor, model, device

    # se não achar, baixa da internet
    
    processor = DPTImageProcessor.from_pretrained("Intel/dpt-hybrid-midas", cache_dir="./models")
    model = DPTForDepthEstimation.from_pretrained("Intel/dpt-hybrid-midas", cache_dir="./models").to(device)
    model.eval()    
    return processor, model, device


def criar_video_depth_3d(img_path, temp=5):
    Path('./renders/temp/').mkdir(parents=True, exist_ok=True)
    nome_base = os.path.splitext(os.path.basename(img_path))[0]
    saida = os.path.join('./renders/temp/', f"{nome_base}_depth.mp4")

    nome_base = os.path.splitext(os.path.basename(img_path))[0]
    depth_path = os.path.join('./outs/', f"{nome_base}_depth.png")
    

    # modelo
    processor, model, device = carregar_modelo_local()
    model.eval()

    # gera mapa de profundidade
    image = Image.open(img_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)
    with torch.no_grad():
        depth = model(**inputs).predicted_depth[0].cpu().numpy()
    depth = (depth - depth.min()) / (depth.max() - depth.min())
    depth_uint8 = (depth * 255).astype(np.uint8)
    Image.fromarray(depth_uint8).save(depth_path)

    # render parallax
    img = cv2.imread(img_path)
    h, w, _ = img.shape
    depth = cv2.imread(depth_path, 0).astype(np.float32) / 255.0
    depth = cv2.resize(depth, (w, h))
    depth = cv2.GaussianBlur(depth, (15, 15), 0)

    focus_x, focus_y = w * 0.5, h * 0.5
    frames, amp, max_zoom, fps = int(temp * 30), 25, 1.12, 30
    map_y, map_x = np.indices((h, w), dtype=np.float32)
    out = cv2.VideoWriter(saida, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    for i in range(frames):
        t = i / frames
        zoom = 1.0 + (max_zoom - 1.0) * np.sin(t * np.pi / 2)
        shift = amp * np.sin(t * np.pi) * (1 - depth)
        cx = focus_x + np.sin(t * np.pi) * 10
        cy = focus_y + np.cos(t * np.pi) * 5
        map_x_zoom = (map_x - cx) / zoom + cx + shift
        map_y_zoom = (map_y - cy) / zoom + cy
        warped = cv2.remap(
            img,
            map_x_zoom.astype(np.float32),
            map_y_zoom.astype(np.float32),
            interpolation=cv2.INTER_LINEAR,
            borderMode=cv2.BORDER_REFLECT
        )
        out.write(warped)
    out.release()

    class Sucesso: filename = saida
    return Sucesso()
