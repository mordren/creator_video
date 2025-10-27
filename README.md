# Sistema de Geração de Conteúdo Automatizado

Sistema modular para geração de roteiros, áudios e vídeos para múltiplos canais, utilizando IA e FFMPEG.

## 🚀 Fluxo de Uso (Comandos Principais)

O fluxo de trabalho é modular e segue a ordem: **Texto (Geração) -> Áudio (Voz/Música) -> Vídeo (Render)**.

**Importante:** Todos os comandos devem ser executados a partir do diretório raiz do projeto. Substitua `<nome_do_canal>` pelo nome do seu canal (ex: `filosofia`) e `<id_roteiro>` pelo ID numérico retornado pelo `texto.py`.

---

### 1. Geração de Roteiro (`texto.py`)

Gera o roteiro, metadados (título, tags) usando a IA e salva no banco de dados.

| Comando | Descrição |
| :--- | :--- |
| **Geração Padrão** | `python texto.py <nome_do_canal>` |
| **Geração com Tema Específico** | `python texto.py <nome_do_canal> --tema "A origem da razão na Grécia Antiga"` |
| **Com Provedor Específico** | `python texto.py <nome_do_canal> --provider gemini` |

**Exemplo:**
```bash
# O sistema retornará o ID do roteiro gerado (ex: ID 42)
python texto.py filosofia