🚀 Como Usar o SistemaO fluxo de trabalho é modular e segue a ordem: Texto (Geração) -> Áudio (Voz/Música) -> Vídeo (Render).1. Geração de Roteiro (texto.py)Este script usa a IA para gerar o roteiro e o salva no banco de dados, retornando o ID do roteiro.ComandoDescriçãoGeração Padrãopython texto.py <nome_do_canal>Geração com Tema Específicopython texto.py <nome_do_canal> --tema "A origem da razão na Grécia Antiga"Com Provedor Específicopython texto.py <nome_do_canal> --provider geminiExemplo:Bash# O sistema deve retornar o ID do roteiro gerado (ex: ID 42)
python texto.py filosofia 
Saída esperada: ... Salvo no banco com ID: 42 ...2. Geração de Áudio e Legenda (audio.py)Este script usa o roteiro salvo (pelo seu ID) para gerar o áudio TTS, a legenda (SRT) e o áudio mixado com a música de fundo.ComandoDescriçãoGeração Padrãopython audio.py <nome_do_canal> <id_roteiro>Com Provedor TTS Específicopython audio.py <nome_do_canal> <id_roteiro> --provider edgeExemplo: (Usando o ID 42 gerado acima)Bashpython audio.py filosofia 42
Saída esperada: ... Áudio mixado criado com sucesso ...3. Geração de Vídeo (video.py)Este script renderiza o vídeo final, buscando o áudio e a legenda gerados e aplicando o template de imagens específico do canal.ComandoDescriçãoRenderizaçãopython video.py <nome_do_canal> <id_roteiro>Exemplo: (Usando o ID 42)Bashpython video.py filosofia 42
Saída esperada: ... SUCESSO! Vídeo ID 42 gerado. ...4. Teste Rápido de Template (gerar_video.py)Use este script para testar rapidamente a renderização de um template específico com um áudio local, sem passar pelo fluxo completo (DB, IA, TTS). Este é o script que você estava editando.ComandoDescriçãoTeste de Renderizaçãopython gerar_video.pyExemplo:Bashpython gerar_video.py
Saída esperada: ✅ Teste concluído: renders_test/video_...mp4🛠️ Alteração no gerar_video.py (Conforme sua solicitação)Para que seu script de teste use as imagens da pasta C:\Users\mordren\Documents\creator\canais\filosofia\assets\imagens_template, o caminho relativo deve ser atualizado.No arquivo gerar_video.py, altere a seção de configuração para:Python# gerar_video.py

# ...
# Configuração para teste
config = {
    # 🎯 CAMINHO ATUALIZADO
    'images_dir': 'canais/filosofia/assets/imagens_template',
    
    'titulo': 'FILOSOFIA MELHORADO',
    'num_imagens': 8,
    'output_dir': './renders_test'
}

# ...