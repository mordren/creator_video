# image.py
#!/usr/bin/env python3
import json
import sys
import argparse
from pathlib import Path
from PIL import Image

sys.path.append(str(Path(__file__).parent))

try:
    from read_config import carregar_config_canal
    from providers.base_imagem import make_image_provider, ImageParams
    from crud.roteiro_manager import RoteiroManager
    from crud.video_manager import VideoManager
    from crud.canal_manager import CanalManager
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    sys.exit(1)

class ImageSystem:
    def __init__(self):
        self.roteiro_manager = RoteiroManager()
        self.video_manager = VideoManager()
        self.canal_manager = CanalManager()

    def _generate_image_prompt(self, roteiro, data: dict) -> str:
        """Gera prompt para imagem baseado no conteúdo do roteiro"""
        
        titulo = data.get('titulo', roteiro.titulo)
        texto = data.get('texto_pt', data.get('texto', roteiro.texto))
        
        # Pega as primeiras palavras para contexto
        texto_resumido = ' '.join(texto.split()[:30])
        
        prompt = f"""
        Crie uma imagem estática de plano de fundo para vídeo sobre: {titulo}
        
        Contexto: {texto_resumido}
        
        A imagem deve ser:
        - Proporção horizontal 16:9 ideal para vídeos longos (largura maior que altura, landscape orientation)
        
        - Estilo clean e profissional
        - Cores harmoniosas que não conflitem com texto sobreposto
        - Temática relacionada ao conteúdo mas não muito específica
        - Adequada para ser plano de fundo de vídeo com legenda
        - Sem texto ou elementos que atrapalhem a legenda
        - Qualidade profissional
        """
        
        return prompt.strip()

    def generate_background_image(self, roteiro_id: int, provider: str = None) -> bool:
        """Gera imagem de fundo para um roteiro pelo ID do banco"""
        print(f"🎨 Gerando imagem de fundo para roteiro ID: {roteiro_id}")
        
        # Busca roteiro no banco
        roteiro = self.roteiro_manager.buscar_por_id(roteiro_id)
        if not roteiro:
            print(f"❌ Roteiro com ID {roteiro_id} não encontrado")
            return False
        
        # Busca canal para obter configuração
        canal = self.canal_manager.buscar_por_id(roteiro.canal_id)
        if not canal:
            print(f"❌ Canal com ID {roteiro.canal_id} não encontrado")
            return False
        
        config = carregar_config_canal(canal.config_path)
        provider = provider or config.get('IMAGE_PROVIDER', 'grok')
        
        # ✅ MESMA ESTRUTURA DO ÁUDIO: Usa id_video do roteiro para construir o caminho
        pasta_base = Path(config['PASTA_BASE'])
        pasta_video = pasta_base / roteiro.id_video
        arquivo_json = pasta_video / f"{roteiro.id_video}.json"
        
        if not arquivo_json.exists():
            print(f"❌ Arquivo JSON não encontrado: {arquivo_json}")
            return False
        
        with open(arquivo_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Gera prompt baseado no conteúdo
        prompt = self._generate_image_prompt(roteiro, data)
        
        # Parâmetros da imagem
        params = ImageParams(
            width=1280,
            height=720,
        )
        
        print(f"🖼️ Gerando imagem | 📺 {data.get('titulo', 'Sem título')}")
        print(f"📁 Pasta: {pasta_video}")
        
        try:
            image_provider = make_image_provider(provider)
            result = image_provider.generate_image(prompt, params, pasta_video)
            
            if result:
                self._update_apos_imagem_sucesso(roteiro, data, result, arquivo_json)
                print(f"✅ Imagem gerada: {result['filepath']}")
                return True
            else:
                print("❌ Falha na geração da imagem")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao gerar imagem: {e}")
            return False

    def _update_apos_imagem_sucesso(self, roteiro, data: dict, image_info: dict, arquivo_json: Path):
        """Atualiza JSON e banco após geração bem-sucedida da imagem, incluindo upscale para resolução maior"""
        
        # Atualiza JSON com info da imagem original
        data.update({
            'imagem_gerada': True,
            'arquivo_imagem_original': image_info['filepath'],  # Renomeado para diferenciar do upscaled
            'imagem_provider': 'xai',
            'imagem_resolucao_original': image_info['resolution']
        })
        
        # Salva JSON inicial
        with open(arquivo_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print("📁 Arquivo JSON atualizado com informações da imagem original")
        
        try:
            # Realiza upscale da imagem para resolução maior (ex: 1920x1080 Full HD)
            upscaled_filepath = self.upscale_image(Path(image_info['filepath']), target_width=1920, target_height=1080)
            
            # Atualiza JSON com info do upscale
            data.update({
                'arquivo_imagem': upscaled_filepath,  # Agora aponta para o upscaled como principal
                'imagem_resolucao': '1920x1080',  # Resolução final após upscale
                'upscale_realizado': True
            })
            
            # Re-salva JSON com updates do upscale
            with open(arquivo_json, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"📈 Upscale realizado: {upscaled_filepath}")
            
            # Atualiza banco de dados (adicione campos no modelo Video se necessário)
            print(f"🔄 Imagem gerada e upscaled para roteiro: {roteiro.id}")
            # Exemplo: self.video_manager.salvar_info_imagem(roteiro.id, {
            #     'arquivo_imagem': upscaled_filepath,
            #     'resolucao': '1920x1080'
            # })
            
        except Exception as e:
            print(f"⚠️ Erro ao atualizar (incluindo upscale): {e}")

    def upscale_image(self, filepath: Path, target_width: int = 1920, target_height: int = 1080) -> str:
        """Função para upscale da imagem usando Pillow com algoritmo de alta qualidade"""
        try:
            img = Image.open(filepath)
            
            # Usa LANCZOS para melhor qualidade em upscale (anti-aliasing)
            upscaled_img = img.resize((target_width, target_height), Image.LANCZOS)
            
            # Nome do arquivo upscaled (ex: original_upscaled.jpg)
            upscaled_path = filepath.parent / f"{filepath.stem}_upscaled{filepath.suffix}"
            upscaled_img.save(upscaled_path, quality=95)  # Salva com alta qualidade JPEG
            
            print(f"✅ Imagem upscaled salva em: {upscaled_path}")
            return str(upscaled_path)
        
        except Exception as upscale_error:
            print(f"❌ Erro no upscale: {upscale_error}")
            raise  # Propaga o erro para o caller tratar

    
def main():
    parser = argparse.ArgumentParser(description='Gerar imagem de fundo para roteiros')
    parser.add_argument('roteiro_id', type=int, help='ID do roteiro no banco')
    parser.add_argument('--provider', help='Provedor de imagem (xai)')
    
    args = parser.parse_args()
    
    success = ImageSystem().generate_background_image(args.roteiro_id, args.provider)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()