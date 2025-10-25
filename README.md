# Sistema de Geração de Conteúdo Automatizado

Sistema modular para geração de roteiros, áudios e vídeos para múltiplos canais, utilizando IA e FFMPEG.

---

## 🚀 Fluxo de Uso (Comandos Principais)

O fluxo de trabalho é modular e segue a ordem: **Texto (Geração) → Áudio (Voz/Música) → Vídeo (Render)**.

> **Importante:** Execute todos os comandos a partir do **diretório raiz** do projeto.  
> Substitua `<nome_do_canal>` (ex.: `filosofia`) e `<id_roteiro>` pelo ID numérico retornado pelo `texto.py`.

---

## 1) Geração de Roteiro (`texto.py`)

Gera o roteiro e metadados (título, tags) usando IA e salva no banco de dados.

| Comando | Descrição |
| :-- | :-- |
| `python texto.py <nome_do_canal>` | Geração padrão |
| `python texto.py <nome_do_canal> --tema "A origem da razão na Grécia Antiga"` | Geração com tema específico |
| `python texto.py <nome_do_canal> --provider gemini` | Geração com provedor específico |

**Exemplo**
```bash
# O sistema retornará o ID do roteiro gerado (ex.: ID 42)
python texto.py filosofia
# Saída esperada (exemplo):
# ... Salvo no banco com ID: 42 ...
```

---

## 2) Geração de Áudio e Legenda (`audio.py`)

Busca o roteiro pelo ID, gera o áudio TTS, a legenda (SRT/ASS) e **mixa** com a música de fundo.

| Comando | Descrição |
| :-- | :-- |
| `python audio.py <nome_do_canal> <id_roteiro>` | Geração padrão |
| `python audio.py <nome_do_canal> <id_roteiro> --provider edge` | Com provedor TTS específico |

**Exemplo (usando o ID 42)**
```bash
python audio.py filosofia 42
# Saída esperada (exemplo):
# ... Áudio mixado criado com sucesso ...
```

---

## 3) Geração de Vídeo (`video.py`)

Renderiza o vídeo final usando o áudio/legenda gerados e aplicando o template de imagens específico do canal.

| Comando | Descrição |
| :-- | :-- |
| `python video.py <nome_do_canal> <id_roteiro>` | Renderização do vídeo final |

**Exemplo (usando o ID 42)**
```bash
python video.py filosofia 42
# Saída esperada:
# 🎉 SUCESSO! Vídeo ID 42 gerado.
```

---

## 4) Teste Rápido de Template (`gerar_video.py`)

Script auxiliar para testar a renderização de um template com um arquivo de áudio **local** pré-existente (sem passar pelo fluxo IA/DB/TTS).

| Comando | Descrição |
| :-- | :-- |
| `python gerar_video.py` | Teste de renderização do template |

**Exemplo**
```bash
python gerar_video.py
# Saída esperada:
# ✅ Teste concluído: .../renders_test/video_...mp4
```

### ⚙️ Configuração de Teste (Importante)

Se estiver usando o script de teste (`gerar_video.py`), confirme que a variável `images_dir` aponta para a pasta correta.

No arquivo `gerar_video.py`:

```python
# gerar_video.py

# ...
# Configuração para teste
config = {
    # 🎯 NOVO CAMINHO PARA SUAS IMAGENS DE TESTE
    'images_dir': 'canais/filosofia/assets/imagens_template',

    'titulo': 'FILOSOFIA MELHORADO',
    'num_imagens': 8,
    'output_dir': './renders_test'
}
# ...
```
---

## Notas

- Certifique-se de que as dependências (bibliotecas Python, FFMPEG, etc.) estejam instaladas e acessíveis no PATH do sistema.
- Os IDs de roteiros são retornados pelo `texto.py` e devem ser usados nos passos de **áudio** e **vídeo**.
- Ajuste provedores de **IA** e **TTS** conforme sua configuração local.
