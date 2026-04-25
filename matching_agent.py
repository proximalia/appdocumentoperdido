"""
Agente de Monitoramento e Matching de Documentos
Este agente monitora continuamente a base de dados e identifica correspondências
entre documentos perdidos e achados
"""

import psycopg2
from datetime import datetime
from typing import List, Dict, Tuple
import time
from difflib import SequenceMatcher


class DocumentMatchingAgent:
    """
    Agente responsável por monitorar e fazer matching entre documentos perdidos e achados
    """

    def __init__(self, db_config: Dict[str, str], check_interval: int = 60):
        """
        Inicializa o agente de matching

        Args:
            db_config: Configurações de conexão com o banco de dados
            check_interval: Intervalo de verificação em segundos (padrão: 60s)
        """
        self.db_config = db_config
        self.check_interval = check_interval
        self.running = False

    def connect_db(self):
        """Estabelece conexão com o banco de dados"""
        return psycopg2.connect(**self.db_config)

    def calculate_similarity_score(self, perdido: Dict, achado: Dict) -> float:
        """
        Calcula score de similaridade entre documento perdido e achado

        Args:
            perdido: Dados do documento perdido
            achado: Dados do documento achado

        Returns:
            Score de 0 a 100 indicando similaridade
        """
        score = 0.0
        max_score = 0.0

        # 1. Tipo de documento (peso 20)
        max_score += 20
        if perdido['tipo_documento'] == achado['tipo_documento']:
            score += 20

        # 2. Número do documento (peso 40)
        max_score += 40
        if perdido['numero_documento'] and achado['numero_documento']:
            if perdido['numero_documento'] == achado['numero_documento']:
                score += 40
            else:
                # Similaridade parcial
                similarity = SequenceMatcher(
                    None,
                    perdido['numero_documento'],
                    achado['numero_documento']
                ).ratio()
                score += similarity * 40

        # 3. Nome do documento (peso 25)
        max_score += 25
        if perdido['nome_documento'] and achado['nome_documento']:
            nome_similarity = SequenceMatcher(
                None,
                perdido['nome_documento'].lower(),
                achado['nome_documento'].lower()
            ).ratio()
            score += nome_similarity * 25

        # 4. CPF do documento (peso 15)
        max_score += 15
        if perdido['cpf_documento'] and achado['cpf_documento']:
            if perdido['cpf_documento'] == achado['cpf_documento']:
                score += 15
            else:
                cpf_similarity = SequenceMatcher(
                    None,
                    perdido['cpf_documento'],
                    achado['cpf_documento']
                ).ratio()
                score += cpf_similarity * 15

        # Normalizar para 0-100
        if max_score > 0:
            final_score = (score / max_score) * 100
        else:
            final_score = 0

        return round(final_score, 2)

    def find_matches(self) -> List[Tuple[Dict, Dict, float]]:
        """
        Busca correspondências entre documentos perdidos e achados

        Returns:
            Lista de tuplas (perdido, achado, score)
        """
        conn = self.connect_db()
        cursor = conn.cursor()

        matches = []

        try:
            # Buscar documentos perdidos ativos
            cursor.execute("""
                SELECT id, usuario_id, tipo_documento, numero_documento,
                       nome_documento, cpf_documento
                FROM documentos_perdidos
                WHERE status = 'perdido'
            """)

            perdidos = cursor.fetchall()

            # Buscar documentos achados disponíveis
            cursor.execute("""
                SELECT id, encontrador_id, tipo_documento, numero_documento,
                       nome_documento, cpf_documento, latitude, longitude,
                       local_encontrado
                FROM documentos_achados
                WHERE status = 'disponivel'
            """)

            achados = cursor.fetchall()

            # Comparar cada documento perdido com cada achado
            for perdido in perdidos:
                perdido_dict = {
                    'id': perdido[0],
                    'usuario_id': perdido[1],
                    'tipo_documento': perdido[2],
                    'numero_documento': perdido[3],
                    'nome_documento': perdido[4],
                    'cpf_documento': perdido[5]
                }

                for achado in achados:
                    achado_dict = {
                        'id': achado[0],
                        'encontrador_id': achado[1],
                        'tipo_documento': achado[2],
                        'numero_documento': achado[3],
                        'nome_documento': achado[4],
                        'cpf_documento': achado[5],
                        'latitude': achado[6],
                        'longitude': achado[7],
                        'local_encontrado': achado[8]
                    }

                    # Calcular similaridade
                    score = self.calculate_similarity_score(perdido_dict, achado_dict)

                    # Se score for alto o suficiente (>= 60%), considerar como match
                    if score >= 60.0:
                        # Verificar se já existe este match
                        cursor.execute("""
                            SELECT id FROM matches
                            WHERE documento_perdido_id = %s
                            AND documento_achado_id = %s
                        """, (perdido_dict['id'], achado_dict['id']))

                        if cursor.fetchone() is None:
                            matches.append((perdido_dict, achado_dict, score))

        finally:
            cursor.close()
            conn.close()

        return matches

    def save_match(self, perdido_id: int, achado_id: int, score: float) -> int:
        """
        Salva um match no banco de dados

        Returns:
            ID do match criado
        """
        conn = self.connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO matches
                (documento_perdido_id, documento_achado_id, score_similaridade)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (perdido_id, achado_id, score))

            match_id = cursor.fetchone()[0]
            conn.commit()

            return match_id

        finally:
            cursor.close()
            conn.close()

    def create_notification(self, match_id: int, usuario_id: int,
                          achado_info: Dict) -> int:
        """
        Cria uma notificação para ser enviada ao usuário

        Returns:
            ID da notificação criada
        """
        conn = self.connect_db()
        cursor = conn.cursor()

        try:
            # Buscar email do usuário
            cursor.execute("""
                SELECT email, nome FROM usuarios WHERE id = %s
            """, (usuario_id,))

            user_data = cursor.fetchone()
            if not user_data:
                return None

            email, nome = user_data

            # Criar mensagem
            assunto = "🎉 Encontramos seu documento!"

            mensagem = f"""
Olá {nome},

Temos ótimas notícias! Acreditamos ter encontrado seu documento!

📄 Tipo: {achado_info['tipo_documento']}
📍 Local onde foi encontrado: {achado_info['local_encontrado']}
🗺️ Coordenadas: {achado_info['latitude']}, {achado_info['longitude']}

Acesse o mapa no aplicativo para ver a localização exata onde o documento
foi deixado pela pessoa que o encontrou.

Por favor, entre em contato o mais breve possível para recuperar seu documento.

Atenciosamente,
Equipe Achados e Perdidos
            """

            # Inserir notificação
            cursor.execute("""
                INSERT INTO notificacoes
                (match_id, usuario_id, tipo, destinatario, assunto, mensagem)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (match_id, usuario_id, 'email', email, assunto, mensagem))

            notificacao_id = cursor.fetchone()[0]
            conn.commit()

            return notificacao_id

        finally:
            cursor.close()
            conn.close()

    def process_matches(self):
        """Processa novos matches encontrados"""
        matches = self.find_matches()

        print(f"[{datetime.now()}] Encontrados {len(matches)} novos matches")

        for perdido, achado, score in matches:
            # Salvar match
            match_id = self.save_match(perdido['id'], achado['id'], score)

            # Criar notificação
            notificacao_id = self.create_notification(
                match_id,
                perdido['usuario_id'],
                achado
            )

            print(f"  ✓ Match criado: ID {match_id}, Score: {score}%, "
                  f"Notificação: {notificacao_id}")

    def run(self):
        """Executa o agente de monitoramento em loop contínuo"""
        self.running = True
        print(f"🤖 Agente de Matching iniciado (intervalo: {self.check_interval}s)")

        while self.running:
            try:
                self.process_matches()
            except Exception as e:
                print(f"❌ Erro ao processar matches: {e}")

            time.sleep(self.check_interval)

    def stop(self):
        """Para a execução do agente"""
        self.running = False
        print("🛑 Agente de Matching parado")


if __name__ == "__main__":
    # Configuração do banco de dados
    db_config = {
        'host': 'localhost',
        'database': 'documentos_db',
        'user': 'postgres',
        'password': 'YOUR_PASSWORD_HERE'
    }

    # Criar e executar agente
    agent = DocumentMatchingAgent(db_config, check_interval=30)

    try:
        agent.run()
    except KeyboardInterrupt:
        agent.stop()
