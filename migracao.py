import sqlalchemy as sa
from sqlmodel import Session, SQLModel, create_engine, text
from app import engine  # Importe do seu app
from sqlalchemy import inspect

def migrar_video_youtube():
    """Migra a tabela VideoYouTube para o novo schema"""
    
    # 1. Verificar a estrutura atual da tabela
    inspector = inspect(engine)
    colunas = inspector.get_columns('videoyoutube')
    colunas_existentes = [col['name'] for col in colunas]
    
    print("Colunas existentes na tabela VideoYouTube:", colunas_existentes)
    
    with Session(engine) as session:
        # 2. Backup dos dados existentes
        if 'roteiro_id' in colunas_existentes:
            print("Fazendo backup dos dados existentes...")
            
            # Buscar todos os registros atuais - CORREÇÃO: usando text()
            resultados = session.execute(
                text("SELECT id, roteiro_id, link, hora_upload, hora_estreia, visualizacoes, likes, comentarios, impressoes, tipo_conteudo FROM videoyoutube")
            )
            dados_backup = resultados.fetchall()
            
            print(f"Encontrados {len(dados_backup)} registros para backup")
            
            # 3. Criar nova tabela temporária - CORREÇÃO: usando text()
            print("Criando nova tabela...")
            session.execute(text("""
                CREATE TABLE IF NOT EXISTS videoyoutube_new (
                    id SERIAL PRIMARY KEY,
                    video_id INTEGER UNIQUE NOT NULL REFERENCES video(id),
                    link TEXT,
                    hora_upload TIMESTAMP,
                    hora_estreia TIMESTAMP,
                    visualizacoes INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    comentarios INTEGER DEFAULT 0,
                    impressoes INTEGER DEFAULT 0,
                    tipo_conteudo VARCHAR(50) DEFAULT 'SHORT'
                )
            """))
            
            # 4. Migrar os dados - mapeando roteiro_id para video_id
            print("Migrando dados...")
            for registro in dados_backup:
                # Verificar se existe um Video com esse roteiro_id - CORREÇÃO: usando text()
                video_result = session.execute(
                    text("SELECT id FROM video WHERE roteiro_id = :roteiro_id"),
                    {"roteiro_id": registro[1]}
                )
                video = video_result.fetchone()
                
                if video:
                    session.execute(
                        text("""
                            INSERT INTO videoyoutube_new 
                            (id, video_id, link, hora_upload, hora_estreia, visualizacoes, likes, comentarios, impressoes, tipo_conteudo)
                            VALUES (:id, :video_id, :link, :hora_upload, :hora_estreia, :visualizacoes, :likes, :comentarios, :impressoes, :tipo_conteudo)
                        """),
                        {
                            "id": registro[0],
                            "video_id": video[0],
                            "link": registro[2],
                            "hora_upload": registro[3],
                            "hora_estreia": registro[4],
                            "visualizacoes": registro[5],
                            "likes": registro[6],
                            "comentarios": registro[7],
                            "impressoes": registro[8],
                            "tipo_conteudo": registro[9] if registro[9] else 'SHORT'
                        }
                    )
            
            # 5. Substituir a tabela antiga pela nova - CORREÇÃO: usando text()
            print("Substituindo tabelas...")
            session.execute(text("DROP TABLE videoyoutube CASCADE"))
            session.execute(text("ALTER TABLE videoyoutube_new RENAME TO videoyoutube"))
            
            # 6. Recriar índices e constraints
            session.execute(text("""
                CREATE INDEX IF NOT EXISTS ix_videoyoutube_video_id ON videoyoutube (video_id)
            """))
            
        else:
            print("A tabela já está com o schema correto")
        
        session.commit()
    print("Migração concluída com sucesso!")

if __name__ == "__main__":
    migrar_video_youtube()