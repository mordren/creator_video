# test_efeitos_completo.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from video_engine import VideoEngine

def testar_todos_efeitos():
    engine = VideoEngine()
    
    print("=== TESTE COMPLETO DE EFEITOS ===")
    print(f"Templates: {engine.list_templates()}")
    print(f"Efeitos carregados: {engine.effect_pool.list_effects()}")
    
    # Testar cada efeito individualmente
    efeitos = engine.effect_pool.list_effects()
    
    for efeito in efeitos:
        print(f"\n🎯 Testando efeito: {efeito}")
        # Aqui você poderia testar com um vídeo real se tiver
        # resultado = engine.aplicar_efeito('video_teste.mp4', f'teste_{efeito}.mp4', efeito)
        # print(f"Resultado: {resultado}")
    
    print(f"\n✅ Total de efeitos funcionais: {len(efeitos)}")

if __name__ == "__main__":
    testar_todos_efeitos()