# youtube_auth.py
import pickle
from pathlib import Path
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow

class YouTubeAuth:
    def __init__(self):
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    
    def autenticar(self, canal_config_path: str):
        """Autentica no YouTube API"""
        try:
            credentials_path = Path('assets/client_secret.json')
            token_path = Path(canal_config_path) / 'token.pickle'
            
            if not credentials_path.exists():
                print(f"❌ Arquivo de credenciais não encontrado: {credentials_path}")
                return None

            creds = self._carregar_credenciais(token_path)
            
            if not creds or not creds.valid:
                creds = self._renovar_credenciais(creds, credentials_path, token_path)
                if not creds:
                    return None

            print("✅ Autenticação no YouTube bem-sucedida")
            return build('youtube', 'v3', credentials=creds)

        except Exception as e:
            print(f"❌ Erro na autenticação: {e}")
            return None

    def _carregar_credenciais(self, token_path: Path):
        """Carrega credenciais existentes do token"""
        if token_path.exists():
            try:
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
                print("✅ Credenciais carregadas do token existente")
                return creds
            except Exception as e:
                print(f"⚠️ Erro ao carregar token: {e}")
        return None

    def _renovar_credenciais(self, creds, credentials_path: Path, token_path: Path):
        """Renova ou obtém novas credenciais"""
        try:
            if creds and creds.expired and creds.refresh_token:
                print("🔄 Refrescando credenciais expiradas...")
                creds.refresh(Request())
            else:
                print("🔐 Iniciando fluxo de autenticação OAuth...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    str(credentials_path), self.SCOPES
                )
                creds = flow.run_local_server(port=0, open_browser=True)
            
            # Salva as credenciais para uso futuro
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
            print("✅ Novas credenciais salvas")
            return creds
            
        except Exception as e:
            print(f"❌ Erro ao renovar credenciais: {e}")
            return None