# texto.py - MODIFICAÇÕES PARA CONTROLE DE TEMPO E PALAVRAS

#!/usr/bin/env python3
import argparse
import json
import sys
import random
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import os

from utils import count_words, obter_proximo_id

# Configura o path para imports
sys.path.append(str(Path(__file__).parent))

logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Silencia logs do TensorFlow se houver
logging.basicConfig(level=logging.ERROR, format='%(message)s')

# ✅ NOVO: Constante para palavras por minuto (ajustável)
PALAVRAS_POR_MINUTO = 140  # Taxa média de fala em português

try:
    from read_config import carregar_config_canal
    from providers.base_texto import make_provider, ModelParams
    # Garantir registro do provider Claude, se disponível
    try:
        from providers import claude_text  # noqa: F401
    except Exception:
        pass
    from utils import extract_json_maybe
    from crud.roteiro_manager import RoteiroManager
    from crud.canal_manager import CanalManager
    from crud.models import Roteiro, Canal
    from sqlmodel import select, Session
except ImportError as e:
    print(f"❌ Erro de importação: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

class TextGenerator:
    def __init__(self):
        self.roteiro_manager = RoteiroManager()
        self.canal_manager = CanalManager()

    def limpar_json_aninhado(self, dados):
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
    
    def remover_tema_do_arquivo(self, tema: str, arquivo_temas: Path):
        """Remove um tema específico do arquivo de temas"""
        try:
            # Lê todos os temas
            with open(arquivo_temas, 'r', encoding='utf-8') as f:
                temas = f.readlines()
            
            # Remove o tema específico
            temas_atualizados = [t.strip() for t in temas if t.strip() != tema]
            
            # Reescreve o arquivo sem o tema removido
            with open(arquivo_temas, 'w', encoding='utf-8') as f:
                f.write('\n'.join(temas_atualizados) + '\n')
            
            print(f"🎲 Tema removido do arquivo: {tema}")
            print(f"📊 Total de temas restantes: {len(temas_atualizados)}")
            
        except Exception as e:
            print(f"❌ Erro ao remover tema do arquivo: {e}")

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

    def carregar_agente(self, config: Dict[str, Any], linha_tema: str = None, 
                        schema: Dict[str, Any] = None, tipo_video: str = 'short',
                        duracao_personalizada: int = None) -> str:
        """Carrega e personaliza o template do agente - ✅ MODIFICADO para aceitar duração personalizada"""
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
                        tema_utilizado = linha_tema                     
                        self.remover_tema_do_arquivo(tema_utilizado, temas_file)                        
                    else:
                        raise ValueError("Arquivo de temas está vazio")
                else:
                    raise FileNotFoundError(f"Arquivo de temas não encontrado: {temas_file}")
            
            # Processa a linha do tema (formato: "autor, assunto")
            partes = [parte.strip() for parte in linha_tema.split(',', 1)]
            
            if len(partes) == 2:
                tema, autor = partes
            else:
                # Se não tem vírgula, usa tudo como tema e autor desconhecido
                tema = partes[0]
                autor = "Reflexão Filosófica"

            # ✅ CARREGA SCHEMA PARA PEGAR CAMPOS E EXEMPLO
            schema_file = pasta_canal / config.get('SCHEMA_FILE', 'schema.json')
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_data = json.load(f)
            
            # ✅ MODIFICADO: Calcula tamanho baseado na duração personalizada ou usa padrão
            if duracao_personalizada:
                duracao_minutos = duracao_personalizada
                # ✅ NOVO: Calcula palavras baseado na duração
                tamanho_max = int(duracao_minutos * PALAVRAS_POR_MINUTO)
                print(f"🎯 Duração personalizada: {duracao_minutos} minutos -> {tamanho_max} palavras")
            else:
                # Comportamento original
                if tipo_video == 'short':
                    tamanho_max = config.get('TAMANHO_MAX_SHORT', 130)
                    duracao_minutos = config.get('DURACAO_MIN_SHORT', 1)
                else:  # long
                    tamanho_max = config.get('TAMANHO_MAX_LONG', 130)
                    duracao_minutos = config.get('DURACAO_MIN_LONG', 3)
            
            # ✅ PREPARA TODAS AS SUBSTITUIÇÕES
            substituicoes = {
                '{tema}': tema,
                '{autor}': autor,
                '{TAMANHO_MAX}': str(tamanho_max),
                '{DURACAO_MINUTOS}': str(duracao_minutos),
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
            print(f"📏 Tamanho máximo: {tamanho_max} palavras")
            print(f"⏱️ Duração: {duracao_minutos} minutos")
            
            return template
            
        except Exception as e:
            print(f"❌ Erro ao carregar agente: {e}")
            raise

    def _construir_json_schema_gemini(self, schema_canal: Dict[str, Any]) -> Dict[str, Any]:
        """Constrói JSON Schema para Gemini baseado no schema do canal"""
        try:
            # Pega o exemplo do schema (pode ser dict ou string)
            exemplo = schema_canal.get('exemplo_resposta', {})
            
            # Se exemplo_resposta é string, tenta converter para dict
            if isinstance(exemplo, str):
                try:
                    # Remove escapes desnecessários
                    exemplo_limpo = exemplo.replace('\\"', '"').replace('\\n', '\n')
                    exemplo = json.loads(exemplo_limpo)
                except json.JSONDecodeError:
                    print("⚠️ Não foi possível converter exemplo_resposta para dict, usando fallback")
                    exemplo = {}
            
            properties = {}
            campos_obrigatorios = schema_canal.get('campos_obrigatorios', [])
            
            for campo in campos_obrigatorios:
                valor_exemplo = exemplo.get(campo)
                
                # Determina o tipo baseado no exemplo ou no nome do campo
                if campo == 'tags' or isinstance(valor_exemplo, list):
                    properties[campo] = {
                        "type": "array", 
                        "items": {"type": "string"}
                    }
                elif campo == 'texto' or campo == 'descricao' or campo == 'titulo' or campo == 'hook' or campo == 'hook_pt' or campo == 'thumb':
                    properties[campo] = {"type": "string"}
                elif isinstance(valor_exemplo, bool):
                    properties[campo] = {"type": "boolean"}
                elif isinstance(valor_exemplo, (int, float)):
                    properties[campo] = {"type": "number"}
                else:
                    # Default para string
                    properties[campo] = {"type": "string"}
            
            # ✅ CORREÇÃO: Remove additionalProperties que não é suportado pelo Gemini
            json_schema = {
                "type": "object",
                "properties": properties,
                "required": campos_obrigatorios
            }
            
            print(f"🎯 JSON Schema gerado para {len(properties)} campos: {list(properties.keys())}")
            return json_schema
            
        except Exception as e:
            print(f"❌ Erro ao construir JSON Schema: {e}")
            # Fallback: schema básico sem additionalProperties
            return {
                "type": "object",
                "properties": {
                    "texto": {"type": "string"},
                    "titulo": {"type": "string"},
                    "descricao": {"type": "string"}
                },
                "required": ["texto", "titulo", "descricao"]
            }

    def gerar_roteiro(self, canal: str, linha_tema: Optional[str] = None, 
                     provider: Optional[str] = None, tipo_video: str = 'short',
                     duracao_minutos: Optional[int] = None) -> Dict[str, Any]:
        """Gera um roteiro completo usando JSON Schema dinâmico - ✅ MODIFICADO para aceitar duração personalizada"""
        try:
            # Carrega configuração do canal
            config = carregar_config_canal(canal)
            schema_canal = self.carregar_schema(config)
            
            # ✅ MODIFICADO: Determina tamanho máximo e resolução baseada no tipo de vídeo E duração personalizada
            if duracao_minutos:
                # ✅ NOVO: Calcula palavras baseado na duração solicitada
                tamanho_texto = int(duracao_minutos * PALAVRAS_POR_MINUTO)
                print(f"🎯 Gerando roteiro com duração personalizada: {duracao_minutos} minutos")
                print(f"   📏 Tamanho calculado: {tamanho_texto} palavras ({PALAVRAS_POR_MINUTO} palavras/minuto)")
            else:
                # Comportamento original
                if tipo_video == 'short':
                    tamanho_texto = config.get('TAMANHO_MAX_SHORT', 130)
                    print(f"🎯 Gerando roteiro para SHORT")
                else:  # long
                    tamanho_texto = config.get('TAMANHO_MAX_LONG', 130)
                    print(f"🎯 Gerando roteiro para LONG")
                print(f"   📏 Tamanho: {tamanho_texto} palavras")
            
            # Determina resolução (não muda com a duração)
            if tipo_video == 'short':
                resolucao = config.get('RESOLUCAO_SHORT', '720x1280')
            else:
                resolucao = config.get('RESOLUCAO_LONG', '1280x720')
            print(f"   📐 Resolução: {resolucao}")

            # Carrega e personaliza prompt do agente - ✅ MODIFICADO: passa duração personalizada
            prompt = self.carregar_agente(config, linha_tema, schema_canal, tipo_video, duracao_minutos)

            # Cria provider
            provider_name = provider or config.get('TEXT_PROVIDER', 'gemini_text')
            texto_provider = make_provider(provider_name)
            
            print(f"🧠 Gerando roteiro com {provider_name.upper()}...")
            
            # ✅ CONSTRÓI JSON SCHEMA DINÂMICO
            json_schema_gemini = self._construir_json_schema_gemini(schema_canal)
            
            # ✅ GERA com JSON Schema dinâmico se for Gemini
            resultado = None
            if provider_name == 'gemini_text' and hasattr(texto_provider, 'generate'):
                print("🎯 Usando JSON Schema nativo do Gemini")
                resultado = texto_provider.generate(prompt, json_schema=json_schema_gemini)
            else:
                print("⚡ Usando método tradicional")
                resultado = texto_provider.generate(prompt)

            # ✅ Para outros providers ou fallback, usa extração tradicional
            if isinstance(resultado, str):
                dados_json = extract_json_maybe(resultado)
                dados_json = self.limpar_json_aninhado(dados_json)
            else:
                dados_json = resultado

            faixa = [int(tamanho_texto * (1 - 0.10)), int(tamanho_texto * (1 + 0.10))]
            attempts = 0
            
            while not faixa[0] <= count_words(dados_json.get('texto', '')) <= faixa[1] and attempts < 6:
                print(f'📊 Tamanho atual: {count_words(dados_json.get("texto", ""))} palavras')
                print('🔄 Refazendo ajuste de tamanho...')
                atual = count_words(dados_json.get('texto', ''))

                if atual < faixa[0]:
                    deficit = faixa[0] - atual
                    print(f"📈 Expandindo (faltam ~{deficit} palavras)")
                    expand_prompt = (
                        "You previously returned this JSON.\n"
                        "Now EXPAND only the field 'texto' to reach a total length close to "
                        f"{tamanho_texto} words (acceptable range {faixa[0]}–{faixa[1]} words). "
                        f"Add about {abs(deficit)} more words by deepening reflection, adding examples, "
                        "and gentle transitions. Do NOT change tone, structure, or metadata. "
                        "Return the FULL JSON again.\n\n"
                        + json.dumps(dados_json, ensure_ascii=False, indent=2)
                    )

                elif atual > faixa[1]:
                    excesso = atual - faixa[1]
                    print(f"📉 Reduzindo (excesso de ~{excesso} palavras)")
                    expand_prompt = (
                        "You previously returned this JSON.\n"
                        "Now REDUCE only the field 'texto' to stay near "
                        f"{tamanho_texto} words (acceptable range {faixa[0]}–{faixa[1]} words). "
                        "Remove redundancies or rephrase lightly to keep natural flow and rhythm. "
                        "Do NOT change tone, structure, or metadata. Return the FULL JSON again.\n\n"
                        + json.dumps(dados_json, ensure_ascii=False, indent=2)
                    )

                # ✅ CORREÇÃO CRÍTICA: Nas tentativas de refazer, também usa JSON Schema
                if provider_name == 'gemini_text' and hasattr(texto_provider, 'generate'):
                    resultado = texto_provider.generate(expand_prompt, json_schema=json_schema_gemini)
                else:
                    resultado = texto_provider.generate(expand_prompt)
                    
                # ✅ Processa o resultado
                if isinstance(resultado, str):
                    dados_json = extract_json_maybe(resultado)
                    dados_json = self.limpar_json_aninhado(dados_json)
                else:
                    dados_json = resultado
                    
                attempts += 1

            # ✅ CORREÇÃO: Valida contra o schema
            if not self.validar_json_contra_schema(dados_json, schema_canal):
                print("❌ JSON não atende ao schema - parando execução")
                return None
            
            # ✅ NOVO: Calcula duração estimada final
            palavras_finais = count_words(dados_json.get('texto', ''))
            duracao_estimada = palavras_finais / PALAVRAS_POR_MINUTO
            
            # Adiciona metadados - ✅ MODIFICADO: inclui duração estimada
            dados_json.update({
                'canal': canal,
                'linha_tema': linha_tema or "aleatório",
                'provider': provider_name,
                'modelo': config.get('MODEL_NAME', 'N/A'),
                'tipo_video': tipo_video,
                'resolucao': resolucao,
                'palavras_geradas': palavras_finais,  # ✅ NOVO
                'duracao_estimada_minutos': round(duracao_estimada, 1)  # ✅ NOVO
            })
            
            print(f"✅ Roteiro finalizado: {palavras_finais} palavras (~{duracao_estimada:.1f} minutos)")
            return dados_json
            
        except Exception as e:
            print(f"❌ Erro na geração do roteiro: {e}")
            import traceback
            traceback.print_exc()
            raise

    def _salvar_no_banco(self, dados: dict, config: dict, tipo_video: str = 'short') -> dict:
        """Salva roteiro no banco de dados usando a nova abordagem com objetos"""
        try:
            # Busca ou cria o canal
            canal = self.canal_manager.buscar_por_nome(config.get('NOME'))
            if not canal:
                # ✅ CORREÇÃO: Extrair valores do config, não passar objetos completos
                canal = Canal(
                    nome=config.get('NOME'),  # String
                    config_path=str(config.get('PASTA_CANAL', '')),  # String
                    link=config.get('LINK')  # String ou None
                )
                canal = self.canal_manager.criar(canal, config)
            
            # ✅ NOVO: Determina resolução baseada no tipo de vídeo
            if tipo_video == 'short':
                resolucao = config.get('RESOLUCAO_SHORT', '720x1280')
            else:  # long
                resolucao = config.get('RESOLUCAO_LONG', '1280x720')
            
            # Cria o objeto Roteiro
            roteiro = Roteiro(
                id_video=dados['id_roteiro'],
                titulo=dados.get('titulo', 'Título temporário'),
                texto=dados.get('texto', ''),
                descricao=dados.get('descricao', ''),
                tags=', '.join(dados.get('tags', [])),
                thumb=dados.get('thumb', 'thumb_temporaria'),
                canal_id=canal.id,
                resolucao=resolucao
            )
            
            # Salva no banco
            roteiro_salvo = self.roteiro_manager.criar(roteiro)
            
            return {'sucesso': True, 'id_banco': roteiro_salvo.id}
                
        except Exception as e:
            return {'sucesso': False, 'erro': str(e)}

    def salvar_roteiro_completo(self, dados: Dict, config: Dict, tipo_video: str = 'short') -> Dict:
        """
        Salva roteiro completo: pasta, arquivos e banco de dados
        """
        pasta_base = Path(config['PASTA_BASE'])
        
        # ✅ CORREÇÃO: Garantir que temos um ID válido
        roteiro_id = dados.get('id_roteiro')
        
        # Se não tem ID ou é inválido, gerar novo
        if not roteiro_id or not roteiro_id.isdigit() or roteiro_id == "Vídeos Automáticos":
            roteiro_id = obter_proximo_id(pasta_base)
            print(f"🆔 Gerado novo ID: {roteiro_id}")
        
        # Cria pasta do roteiro
        pasta_roteiro = pasta_base / roteiro_id
        pasta_roteiro.mkdir(parents=True, exist_ok=True)
        
        # Atualiza dados com ID do roteiro
        dados['id_roteiro'] = roteiro_id
        dados['canal'] = config.get('NOME')
        
        # Salva arquivos
        caminho_json = pasta_roteiro / f"{roteiro_id}.json"
        with open(caminho_json, 'w', encoding='utf-8') as f:
            json.dump(dados, f, ensure_ascii=False, indent=2)
        
        # Salva texto em arquivo .txt
        caminho_txt = pasta_roteiro / f"{roteiro_id}.txt"
        texto_pt = dados.get("texto_pt", dados.get("texto", ""))
        with open(caminho_txt, 'w', encoding='utf-8') as f:
            f.write(texto_pt)
        
        # Salva no banco de dados
        resultado_db = self._salvar_no_banco(dados, config, tipo_video)
        
        return {
            'id_roteiro': roteiro_id,
            'pasta_roteiro': pasta_roteiro,
            'arquivo_json': caminho_json,
            'arquivo_txt': caminho_txt,
            'dados': dados,
            'db_result': resultado_db
        }

def main():
    parser = argparse.ArgumentParser(description='Gerar roteiros usando IA')
    parser.add_argument('canal', help='Nome do canal')
    parser.add_argument('linha_tema', nargs='?', help='Tema no formato "autor, assunto" (opcional - usa aleatório se não informado)')
    parser.add_argument('tipo_video', choices=['short', 'long'], default='short', 
                       help='Tipo de vídeo a ser gerado (short ou long)')
    parser.add_argument('--provider', help='Provedor de IA (gemini, grok, claude)')
    # ✅ NOVO: Argumento para duração personalizada
    parser.add_argument('--duracao', type=int, help='Duração desejada do vídeo em minutos (sobrescreve configuração padrão)')
    
    args = parser.parse_args()
    
    try:
        generator = TextGenerator()
        
        # Gera roteiro (com tema aleatório se não especificado) - ✅ MODIFICADO: passa duração personalizada
        roteiro = generator.gerar_roteiro(args.canal, args.linha_tema, args.provider, args.tipo_video, args.duracao)
        
        if not roteiro:
            print("❌ Falha na geração do roteiro")
            return 1
        
        print(f"\n🎬 Roteiro gerado com sucesso!")
        print(f"📺 Título: {roteiro.get('titulo', 'N/A')}")
        print(f"📝 Descrição: {roteiro.get('descricao', 'N/A')}")
        print(f"🏷️ Tags: {', '.join(roteiro.get('tags', []))}")
        print(f"🎯 Tipo: {roteiro.get('tipo_video', 'N/A')}")
        print(f"📐 Resolução: {roteiro.get('resolucao', 'N/A')}")
        # ✅ NOVO: Mostra informações de duração
        print(f"📊 Palavras: {roteiro.get('palavras_geradas', 'N/A')}")
        print(f"⏱️ Duração estimada: {roteiro.get('duracao_estimada_minutos', 'N/A')} minutos")
        
        # Salva o roteiro
        config = carregar_config_canal(args.canal)
        resultado_salvo = generator.salvar_roteiro_completo(roteiro, config, args.tipo_video)

        if resultado_salvo['db_result'].get('sucesso'):
            print(f"💾 Salvo no banco com ID: {resultado_salvo['db_result'].get('id_banco', 'N/A')}")
            print(f"📁 Pasta: {resultado_salvo['pasta_roteiro']}")
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
