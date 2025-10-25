# test_capa.py
#!/usr/bin/env python3
import subprocess
from pathlib import Path

def quebrar_texto(texto, max_caracteres=20):
    """Quebra o texto em múltiplas linhas de forma inteligente"""
    palavras = texto.split()
    if not palavras:
        return texto
    
    linhas = []
    linha_atual = []
    
    for palavra in palavras:
        linha_teste = ' '.join(linha_atual + [palavra])
        
        if len(linha_teste) <= max_caracteres:
            linha_atual.append(palavra)
        else:
            if linha_atual:
                linhas.append(' '.join(linha_atual))
            
            if len(palavra) > max_caracteres:
                partes = [palavra[i:i+max_caracteres-3] + "..." for i in range(0, len(palavra), max_caracteres-3)]
                linha_atual = [partes[0]]
                linhas.extend(partes[1:])
            else:
                linha_atual = [palavra]
    
    if linha_atual:
        linhas.append(' '.join(linha_atual))
    
    linhas = [linha.strip() for linha in linhas if linha.strip()]
    return '\n'.join(linhas)

def gerar_capa_quebrada(imagem_path, texto_quebrado, output_path, largura=720, altura=1280):
    """Gera capa com texto quebrado centralizado na metade superior"""
    try:
        # Escapar caracteres especiais
        texto_escapado = texto_quebrado.replace("'", "'\\''")
        
        # Dividir o texto em linhas
        linhas = texto_quebrado.split('\n')
        num_linhas = len(linhas)
        
        print(f"📝 Gerando capa com {num_linhas} linhas:")
        for i, linha in enumerate(linhas):
            print(f"   Linha {i+1}: '{linha}'")
        
        # Calcular posição Y inicial para centralizar na metade superior
        altura_metade_superior = altura // 2
        offset_y = (altura_metade_superior - (num_linhas * 50)) // 2
        
        # Construir múltiplos comandos drawtext, um para cada linha
        drawtext_commands = []
        for i, linha in enumerate(linhas):
            if linha.strip():
                y_pos = offset_y + (i * 50)  # 50 pixels entre linhas
                
                drawtext_cmd = (
                    f"drawtext=text='{linha.strip()}':"
                    f"font='Arial':fontsize=55:"  # Usando Arial que é mais comum
                    f"fontcolor=#6B10D3:borderw=3:bordercolor=#FFFFFF:"
                    f"x=(w-text_w)/2:y={y_pos}"
                )
                drawtext_commands.append(drawtext_cmd)
        
        # Juntar todos os comandos drawtext
        filter_complex = (
            f"scale={largura}:{altura}:force_original_aspect_ratio=decrease,"
            f"pad={largura}:{altura}:(ow-iw)/2:(oh-ih)/2:color=black,"
            + ",".join(drawtext_commands)
        )
        
        cmd = [
            "ffmpeg", "-y",
            "-i", str(imagem_path),
            "-vf", filter_complex,
            "-frames:v", "1",
            str(output_path)
        ]
        
        print("🎨 Executando FFmpeg...")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(f"✅ Capa gerada com sucesso: {output_path}")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro no FFmpeg: {e}")
        print(f"Stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Erro geral: {e}")
        return False

def testar_capa():
    """Testa a geração de capa com diferentes textos"""
    
    # Textos de teste
    textos_teste = [
        "Uma reflexão profunda sobre a vida e o universo",
        "Como a filosofia estoica pode transformar seu dia a dia",
        "Os segredos da mente humana revelados pela psicologia moderna",
        "Viver no presente: o caminho para a felicidade genuína",
        "Teste muito longo para ver como a quebra funciona com palavras extremamente grandes"
    ]
    
    # Imagem de teste (use qualquer imagem que você tenha)
    imagem_teste = Path("test_image.jpg")  # Altere para uma imagem real
    
    if not imagem_teste.exists():
        print("❌ Imagem de teste não encontrada. Criando imagem simples...")
        # Cria uma imagem simples para teste
        cmd_criar_imagem = [
            "ffmpeg", "-y",
            "-f", "lavfi",
            "-i", "color=color=darkblue:size=720x1280",
            "-frames:v", "1",
            str(imagem_teste)
        ]
        try:
            subprocess.run(cmd_criar_imagem, check=True, capture_output=True)
            print("✅ Imagem de teste criada")
        except:
            print("❌ Não foi possível criar imagem de teste")
            return
    
    for i, texto in enumerate(textos_teste):
        print(f"\n{'='*50}")
        print(f"TESTE {i+1}: {texto}")
        print(f"{'='*50}")
        
        # Quebrar o texto
        texto_quebrado = quebrar_texto(texto, max_caracteres=20)
        
        # Gerar capa
        output_path = Path(f"capa_teste_{i+1}.png")
        sucesso = gerar_capa_quebrada(imagem_teste, texto_quebrado, output_path)
        
        if sucesso and output_path.exists():
            print(f"🎉 Teste {i+1} concluído com sucesso!")
            print(f"📁 Arquivo: {output_path}")
        else:
            print(f"❌ Teste {i+1} falhou")

if __name__ == "__main__":
    print("🧪 TESTE DE GERAÇÃO DE CAPA COM TEXTO QUEBRADO")
    print("Este teste verifica se o texto é quebrado corretamente e centralizado na metade superior")
    
    testar_capa()
    
    print("\n🎯 TESTE CONCLUÍDO!")
    print("Verifique os arquivos capa_teste_*.png gerados")