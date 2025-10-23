# video_engine.py
from pathlib import Path
from typing import Dict, Any
import importlib.util
import sys

class EffectPool:
    def __init__(self):
        self.effects = {}
        self._load_effects()
    
    def _load_effects(self):
        """Carrega efeitos que têm função 'aplicar' (para aplicar em vídeos)"""
        effects_dir = Path(__file__).parent / "efeitos"
        
        if not effects_dir.exists():
            print("⚠️ Pasta 'efeitos' não encontrada")
            return
        
        for effect_file in effects_dir.glob("*.py"):
            if effect_file.name == "__init__.py":
                continue
                
            effect_name = effect_file.stem
            try:
                spec = importlib.util.spec_from_file_location(effect_name, effect_file)
                effect_module = importlib.util.module_from_spec(spec)
                sys.modules[effect_name] = effect_module
                spec.loader.exec_module(effect_module)
                
                # Procura função 'aplicar' para aplicar em vídeos existentes
                if hasattr(effect_module, 'aplicar'):
                    self.effects[effect_name] = effect_module.aplicar
                    print(f"✅ Efeito carregado: {effect_name}")
                else:
                    print(f"⚠️ Efeito sem função 'aplicar': {effect_name}")
                    
            except Exception as e:
                print(f"❌ Erro ao carregar efeito {effect_name}: {e}")
                
    def apply_effect(self, effect_name: str, video_input: str, video_output: str) -> bool:
        """Aplica um efeito específico"""
        if effect_name not in self.effects:
            print(f"❌ Efeito não encontrado: {effect_name}")
            return False
        
        try:
            return self.effects[effect_name](video_input, video_output)
        except Exception as e:
            print(f"❌ Erro ao aplicar efeito {effect_name}: {e}")
            return False
    
    def list_effects(self):
        return list(self.effects.keys())

class VideoEngine:
    def __init__(self):
        self.templates = {}
        self.effect_pool = EffectPool()
        self.efeitos_carregados = self.effect_pool.effects  # Aponta para os efeitos do pool
        self._load_templates()
    
    def _load_templates(self):
        """Carrega templates da pasta templates"""
        templates_dir = Path(__file__).parent / "templates"
        
        if not templates_dir.exists():
            print("⚠️ Pasta 'templates' não encontrada")
            return
        
        for template_file in templates_dir.glob("*.py"):
            if template_file.name == "__init__.py":
                continue
                
            template_name = template_file.stem
            try:
                spec = importlib.util.spec_from_file_location(template_name, template_file)
                template_module = importlib.util.module_from_spec(spec)
                sys.modules[template_name] = template_module
                spec.loader.exec_module(template_module)
                
                if hasattr(template_module, 'render'):
                    self.templates[template_name] = template_module.render
                    print(f"✅ Template carregado: {template_name}")
                else:
                    print(f"⚠️ Template sem função 'render': {template_name}")
                    
            except Exception as e:
                print(f"❌ Erro ao carregar template {template_name}: {e}")
    
    def list_templates(self):
        return list(self.templates.keys())
    
    def render_video(self, template_name: str, audio_path: str, config: Dict[str, Any]) -> Path:
        """Renderiza um vídeo usando um template específico"""
        if template_name not in self.templates:
            available = self.list_templates()
            raise ValueError(f"Template '{template_name}' não encontrado. Disponíveis: {available}")
        
        print(f"🎬 Renderizando com template: {template_name}")
        return self.templates[template_name](audio_path, config)

    def aplicar_efeito(self, video_input: str, video_output: str, efeito_nome: str) -> bool:
        """Aplica um efeito específico a um vídeo"""
        return self.effect_pool.apply_effect(efeito_nome, video_input, video_output)

# Instância global
engine = VideoEngine()