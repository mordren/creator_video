# texto.py
#!/usr/bin/env python3
import argparse
import json
import sys
import random
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import os

from utils import count_words

# Configura o path para imports
sys.path.append(str(Path(__file__).parent))

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Silencia logs do TensorFlow se houver
logging.basicConfig(level=logging.ERROR, format='%(message)s')

try:
    from read_config import carregar_config_canal
    from providers.base_texto import make_provider, ModelParams
    from utils import extract_json_maybe
    from crud.manager import DatabaseManager
    from crud.video_manager import VideoManager
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

class TextGenerator:
    def __init__(self):
        try:
            self.db = DatabaseManager()
        except Exception as e:
            print(f"⚠️ Aviso: Não foi possível conectar ao banco: {e}")
            self.db = None

    
    def limpar_json_aninhado(self,dados):
        """Remove JSON aninhado dentro de 'texto' e deixa só o texto puro."""
        import re, json
        if not isinstance(dados, dict):
            return dados
        texto = dados.get("texto", "")
        if isinstance(texto, str):
            # remove cercas markdown e ```json
            texto_limpo = re.sub(r"^```json|```$", "", texto.strip(), flags=re.IGNORECASE)
            # tenta decodificar se ainda for um JSON stringificado
            try:
                interno = json.loads(texto_limpo)
                if isinstance(interno, dict) and "texto" in interno:
                    texto_limpo = interno["texto"]
            except Exception:
                pass
            # desescapa aspas e \n
            texto_limpo = texto_limpo.replace('\\"', '"').replace('\\\\n', '\n')
            dados["texto"] = texto_limpo.strip()
        return dados

    
    def carregar_schema(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Carrega o schema de validação do canal"""
        try:
            pasta_canal = config['PASTA_CANAL']
            schema_file = pasta_canal / config.get('SCHEMA_FILE', 'schema.json')
            
            if not schema_file.exists():
                raise FileNotFoundError(f"Arquivo schema não encontrado: {schema_file}")
            
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            print(f"📋 Schema carregado: {len(schema.get('campos_obrigatorios', []))} campos obrigatórios")
            return schema
            
        except Exception as e:
            print(f"❌ Erro ao carregar schema: {e}")
            raise

    def validar_json_contra_schema(self, dados: Dict[str, Any], schema: Dict[str, Any]) -> bool:
        """Valida se o JSON gerado pela IA segue o schema do canal"""
        campos_obrigatorios = schema.get('campos_obrigatorios', [])
        
        if not campos_obrigatorios:
            print("⚠️ Schema sem campos obrigatórios definidos")
            return True
        
        campos_faltantes = [campo for campo in campos_obrigatorios if campo not in dados]
        
        if campos_faltantes:
            print(f"❌ Campos obrigatórios faltando: {campos_faltantes}")
            print(f"📋 Campos esperados: {campos_obrigatorios}")
            print(f"📦 Campos recebidos: {list(dados.keys())}")
            return False
        
        print("✅ JSON validado contra schema com sucesso")
        return True

    def carregar_agente(self, config: Dict[str, Any], linha_tema: str = None, schema: Dict[str, Any] = None) -> str:
        """Carrega e personaliza o template do agente"""
        try:
            pasta_canal = config['PASTA_CANAL']
            agente_file = pasta_canal / config.get('AGENTE_FILE', 'agente.txt')
            
            if not agente_file.exists():
                raise FileNotFoundError(f"Arquivo do agente não encontrado: {agente_file}")
            
            template = agente_file.read_text(encoding='utf-8')
            
            # Se não foi passado um tema, pega um aleatório do arquivo de temas
            if not linha_tema:
                temas_file = pasta_canal / config.get('TEMAS_FILE', 'temas.txt')
                if temas_file.exists():
                    temas = temas_file.read_text(encoding='utf-8').strip().split('\n')
                    temas = [tema.strip() for tema in temas if tema.strip()]
                    if temas:
                        linha_tema = random.choice(temas)
                        print(f"🎲 Tema aleatório selecionado: {linha_tema}")
                    else:
                        raise ValueError("Arquivo de temas está vazio")
                else:
                    raise FileNotFoundError(f"Arquivo de temas não encontrado: {temas_file}")
            
            # Processa a linha do tema (formato: "autor, assunto")
            partes = [parte.strip() for parte in linha_tema.split(',', 1)]
            
            # CORREÇÃO: Deve ser:
            if len(partes) == 2:
                tema, autor = partes  # ← CORRETO: tema primeiro, autor depois
            else:
                # Se não tem vírgula, usa tudo como tema e autor desconhecido
                tema = partes[0]
                autor = "Reflexão Filosófica"

    # ✅ CARREGA SCHEMA PARA PEGAR CAMPOS E EXEMPLO
            schema_file = pasta_canal / config.get('SCHEMA_FILE', 'schema.json')
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
            
            # ✅ PREPARA TODAS AS SUBSTITUIÇÕES
            substituicoes = {
                '{tema}': tema,
                '{autor}': autor,
                '{TAMANHO_MAX}': str(config.get('TAMANHO_MAX', 135)),
                '{DURACAO_MINUTOS}': str(config.get('DURACAO_MINUTOS', 1)),
                '{campos_obrigatorios}': str(schema_data.get('campos_obrigatorios', [])),
                '{exemplo_resposta}': schema_data.get('exemplo_resposta', '')
            }
            
            # ✅ SUBSTITUI TODOS OS PLACEHOLDERS NO TEMPLATE
            for placeholder, valor in substituicoes.items():
                if not isinstance(valor, str):
                    valor = json.dumps(valor, ensure_ascii=False, indent=2)
                template = template.replace(placeholder, valor)

            
            print(f"🎯 Tema: {tema}")
            print(f"👤 Autor: {autor if autor else '(não especificado)'}")
            
            return template
            
        except Exception as e:
            print(f"❌ Erro ao carregar agente: {e}")
            raise


    def gerar_roteiro(self, canal: str, linha_tema: Optional[str] = None, provider: Optional[str] = None) -> Dict[str, Any]:
        """Gera um roteiro completo usando o provider configurado"""
        try:
            # Carrega configuração do canal
            config = carregar_config_canal(canal)
            schema = self.carregar_schema(config)
            tamanho_texto = config.get('TAMANHO_MAX')

            # Carrega e personaliza prompt do agente (com tema aleatório se não especificado)
            prompt = self.carregar_agente(config, linha_tema, schema)

            # Cria provider (usa o da config se não especificado)
            provider_name = provider or config.get('TEXT_PROVIDER', 'gemini')
            texto_provider = make_provider(provider_name)
            
            print(f"🧠 Gerando roteiro com {provider_name.upper()}...")            
            
            # Gera conteúdo
            resultado = texto_provider.generate(prompt)

            # ✅ CORREÇÃO CRÍTICA: Extrai e valida JSON
            test = extract_json_maybe(resultado)
            dados_json = self.limpar_json_aninhado(test)

            faixa = [int(tamanho_texto * (1 - 0.05)), int(tamanho_texto * (1 + 0.05))]
            attempts = 0
            while not faixa[0] <= count_words(dados_json.get('texto', '')) <= faixa[1] and attempts < 3:
                print('tamanho:' + str(count_words(dados_json.get('texto'))))
                print('Refazendo')
                atual = count_words(dados_json.get('texto', ''))

                if atual < faixa[0]:
                    deficit = faixa[0] - atual
                    print(f"Refazendo (faltam ~{deficit} palavras)")
                    expand_prompt = (
                        "You previously returned this JSON.\n"
                        "Expand ONLY the 'texto' field by ADDING new paragraphs (no headings), "
                        f"with at least {deficit} more words. Keep tone and cadence. "
                        "Return FULL JSON with updated 'texto' and 'palavras'.\n\n"
                        + json.dumps(dados_json, ensure_ascii=False, indent=2)
                    )

                elif atual > faixa[1]:
                    excesso = atual - faixa[1]
                    print(f"Reduzindo (excesso de ~{excesso} palavras)")
                    expand_prompt = (
                        "You previously returned this JSON.\n"
                        "Tighten ONLY the 'texto' field by merging repetitions and trimming gently, "
                        f"removing about {excesso} words. Keep tone and cadence. "
                        "Return FULL JSON with updated 'texto' and 'palavras'.\n\n"
                        + json.dumps(dados_json, ensure_ascii=False, indent=2)
                    )

                resultado = texto_provider.generate(expand_prompt)
                test = extract_json_maybe(resultado)
                dados_json = self.limpar_json_aninhado(test)
                attempts += 1

                
            
            # ✅ GARANTE que dados_json é um dict
            if not isinstance(dados_json, dict):
                print(f"❌ ERRO CRÍTICO: extract_json_maybe retornou não-dict: {type(dados_json)}")
                dados_json = {
                    "texto": str(dados_json) if dados_json else "Conteúdo não disponível",
                    "titulo": "Spiritual Reflection",
                    "descricao": "A moment of prayer and reflection",
                    "hook": "Find peace in prayer",
                    "hook_pt": "Encontre paz na oração",
                    "thumb": "prayer peace reflection",
                    "tags": ["#prayer", "#faith", "#christian", "#peace", "#reflection"]
                }

            # ✅ CORREÇÃO: Valida contra o schema
            if not self.validar_json_contra_schema(dados_json, schema):
                print("❌ JSON não atende ao schema - parando execução")
                return None
            
            
            # Adiciona metadados
            dados_json.update({
                'canal': canal,
                'linha_tema': linha_tema or "aleatório",
                'provider': provider_name,
                'modelo': config.get('MODEL_NAME', 'N/A')
            })
            
            return dados_json  # ✅ CORREÇÃO: Retorna dados_json, não resultado
            
        except Exception as e:
            print(f"❌ Erro na geração do roteiro: {e}")
            import traceback
            traceback.print_exc()
            raise

    def salvar_roteiro_completo(self, dados: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Salva roteiro no banco e sistema de arquivos"""
        try:
            # Inicializa gerenciador de vídeos
            video_manager = VideoManager(config['PASTA_BASE'])
            
            # Salva no sistema de arquivos e banco
            resultado = video_manager.salvar_video_completo(dados, dados['canal'], config)
            
            print(f"✅ Roteiro salvo com ID: {resultado['id_video']}")
            print(f"📁 Pasta: {resultado['pasta_video']}")
            
            return resultado
            
        except Exception as e:
            print(f"❌ Erro ao salvar roteiro: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Gerar roteiros usando IA')
    parser.add_argument('canal', help='Nome do canal')
    parser.add_argument('linha_tema', nargs='?', help='Tema no formato "autor, assunto" (opcional - usa aleatório se não informado)')
    parser.add_argument('--provider', help='Provedor de IA (gemini, grok, claude)')    
    
    args = parser.parse_args()
    
    try:
        generator = TextGenerator()
        
        # Gera roteiro (com tema aleatório se não especificado)
        roteiro = generator.gerar_roteiro(args.canal, args.linha_tema, args.provider)
        
        print(f"\n🎬 Roteiro gerado com sucesso!")
        print(f"📺 Título: {roteiro.get('titulo', 'N/A')}")
        print(f"📝 Descrição: {roteiro.get('descricao', 'N/A')}")
        print(f"🏷️ Tags: {', '.join(roteiro.get('tags', []))}")
        print(f"📊 Palavras-chave thumb: {roteiro.get('thumbnail_palavras', [])}")
        
        # Salva se solicitado

        config = carregar_config_canal(args.canal)
        resultado_salvo = generator.salvar_roteiro_completo(roteiro, config)
        if resultado_salvo['db_result'].get('sucesso'):
            print(f"💾 Salvo no banco com ID: {resultado_salvo['db_result'].get('id_banco', 'N/A')}")
        else:
            print(f"⚠️ Erro ao salvar no banco: {resultado_salvo['db_result'].get('erro')}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())