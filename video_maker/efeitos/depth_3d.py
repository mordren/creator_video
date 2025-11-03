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
    print("📥 Baixando modelo da internet...")
    Path("./models").mkdir(parents=True, exist_ok=True)
    processor = DPTImageProcessor.from_pretrained("Intel/dpt-hybrid-midas", cache_dir="./models")
    model = DPTForDepthEstimation.from_pretrained("Intel/dpt-hybrid-midas", cache_dir="./models").to(device)
    model.eval()    
    return processor, model, device


def criar_video_depth_3d(img_path, temp=5):
    # Cria TODOS os diretórios necessários ANTES de usar
    Path('./renders/temp/').mkdir(parents=True, exist_ok=True)
    Path('./outs/').mkdir(parents=True, exist_ok=True)  # ← ESTA LINHA ESTAVA FALTANDO
    
    nome_base = os.path.splitext(os.path.basename(img_path))[0]
    saida = os.path.join('./renders/temp/', f"{nome_base}_depth.mp4")
    depth_path = os.path.join('./outs/', f"{nome_base}_depth.png")

    # modelo
    processor, model, device = carregar_modelo_local()

    # gera mapa de profundidade
    image = Image.open(img_path).convert("RGB")
    inputs = processor(images=image, return_tensors="pt").to(device)
    
    with torch.no_grad():
        outputs = model(**inputs)
        depth = outputs.predicted_depth[0].cpu().numpy()

    depth = (depth - depth.min()) / (depth.max() - depth.min())
    depth_uint8 = (depth * 255).astype(np.uint8)
    
    # Agora o diretório existe, então pode salvar
    Image.fromarray(depth_uint8).save(depth_path)
    print(f"✅ Mapa de profundidade salvo em: {depth_path}")

    # render parallax
    img = cv2.imread(img_path)
    if img is None:
        raise ValueError(f"Erro ao carregar imagem: {img_path}")
        
    h, w, _ = img.shape
    depth_map = cv2.imread(depth_path, cv2.IMREAD_GRAYSCALE)
    if depth_map is None:
        raise ValueError(f"Erro ao carregar mapa de profundidade: {depth_path}")
        
    depth_map = depth_map.astype(np.float32) / 255.0
    depth_map = cv2.resize(depth_map, (w, h))
    depth_map = cv2.GaussianBlur(depth_map, (15, 15), 0)

    focus_x, focus_y = w * 0.5, h * 0.5
    frames, amp, max_zoom, fps = int(temp * 30), 25, 1.12, 30
    map_y, map_x = np.indices((h, w), dtype=np.float32)
    
    # Configuração do video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(saida, fourcc, fps, (w, h))

    # Frequências em Hz (ciclos por segundo) para manter movimento consistente
    # independente da duração total do clipe.
    f_zoom = 0.12        # ~8.3s por ciclo – zoom suave
    f_shift = 0.33       # ~3.0s por ciclo – parallax perceptível
    f_pan = 0.18         # ~5.6s por ciclo – leve pan

    # Ajuste de amplitude com base no tamanho da imagem (mantém proporção em resoluções diferentes)
    base = min(w, h)
    amp_px = max(12, int(0.02 * base))  # ~2% do menor lado, mínimo 12px
    pan_x_amp = max(8, int(0.015 * w))
    pan_y_amp = max(4, int(0.008 * h))

    # Envelopes de entrada/saída para evitar cortes abruptos
    fade_secs = 0.35
    fade_frames = int(fade_secs * fps)

    for i in range(frames):
        # tempo absoluto em segundos (não normalizado pela duração)
        t_sec = i / fps

        # janela suave de entrada/saída (cosine fade)
        fade_in = 1.0 if i >= fade_frames else 0.5 * (1 - np.cos(np.pi * (i / max(1, fade_frames))))
        fade_out = 1.0 if (frames - 1 - i) >= fade_frames else 0.5 * (1 - np.cos(np.pi * ((frames - 1 - i) / max(1, fade_frames))))
        env = min(fade_in, fade_out)

        # zoom oscila lentamente entre 1.0 e max_zoom
        zoom = 1.0 + (max_zoom - 1.0) * (0.5 + 0.5 * np.sin(2 * np.pi * f_zoom * t_sec)) * env

        # deslocamento de parallax periódico (profundidades mais próximas movem mais)
        shift = (amp_px * (0.75 + 0.25 * np.sin(2 * np.pi * f_shift * t_sec))) * (1 - depth_map) * env

        # leve pan em X/Y para dar sensação de câmera
        cx = focus_x + pan_x_amp * np.sin(2 * np.pi * f_pan * t_sec)
        cy = focus_y + pan_y_amp * np.cos(2 * np.pi * f_pan * t_sec)
        
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
    print(f"✅ Vídeo 3D salvo em: {saida}")

    class Sucesso: 
        filename = saida
        
    return Sucesso()
