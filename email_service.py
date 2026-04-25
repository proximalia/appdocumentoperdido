"""
Serviço de envio de notificações por email
Integração com CREAO Gmail MCP
"""

import psycopg2
from datetime import datetime
from typing import Dict, Optional


class EmailNotificationService:
    """
    Serviço responsável por processar e enviar notificações por email
    """

    def __init__(self, db_config: Dict[str, str]):
        """
        Inicializa o serviço de email

        Args:
            db_config: Configurações de conexão com o banco de dados
        """
        self.db_config = db_config

    def connect_db(self):
        """Estabelece conexão com o banco de dados"""
        return psycopg2.connect(**self.db_config)

    def get_pending_notifications(self) -> list:
        """
        Busca notificações pendentes de envio

        Returns:
            Lista de notificações pendentes
        """
        conn = self.connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, match_id, usuario_id, destinatario, assunto, mensagem
                FROM notificacoes
                WHERE enviado = FALSE AND tipo = 'email'
                ORDER BY criado_em ASC
                LIMIT 10
            """)

            notifications = []
            for row in cursor.fetchall():
                notifications.append({
                    'id': row[0],
                    'match_id': row[1],
                    'usuario_id': row[2],
                    'destinatario': row[3],
                    'assunto': row[4],
                    'mensagem': row[5]
                })

            return notifications

        finally:
            cursor.close()
            conn.close()

    def send_email(self, to: str, subject: str, body: str) -> Dict:
        """
        Envia email usando CREAO Gmail MCP

        Args:
            to: Destinatário
            subject: Assunto
            body: Corpo do email

        Returns:
            Resultado do envio
        """
        # NOTA: Esta função deve ser integrada com o CREAO Gmail MCP
        # Por enquanto, é um mock que simula o envio

        print(f"\n📧 Enviando email para: {to}")
        print(f"   Assunto: {subject}")
        print(f"   Corpo:\n{body}\n")

        # Em produção, usar:
        # resultado = creao_gmail_mcp.send_email(
        #     to=to,
        #     subject=subject,
        #     body=body
        # )

        # Mock de resposta bem-sucedida
        return {
            'success': True,
            'message_id': f'msg_{datetime.now().timestamp()}'
        }

    def mark_notification_sent(self, notification_id: int, success: bool,
                              error: Optional[str] = None):
        """
        Marca notificação como enviada no banco de dados

        Args:
            notification_id: ID da notificação
            success: Se o envio foi bem-sucedido
            error: Mensagem de erro, se houver
        """
        conn = self.connect_db()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                UPDATE notificacoes
                SET enviado = %s,
                    data_envio = %s,
                    erro = %s
                WHERE id = %s
            """, (success, datetime.now(), error, notification_id))

            # Se enviado com sucesso, marcar match como notificado
            if success:
                cursor.execute("""
                    UPDATE matches
                    SET notificacao_enviada = TRUE,
                        data_notificacao = %s
                    WHERE id = (
                        SELECT match_id FROM notificacoes WHERE id = %s
                    )
                """, (datetime.now(), notification_id))

            conn.commit()

        finally:
            cursor.close()
            conn.close()

    def process_notifications(self):
        """Processa e envia notificações pendentes"""
        notifications = self.get_pending_notifications()

        print(f"[{datetime.now()}] Processando {len(notifications)} notificações")

        for notification in notifications:
            try:
                # Enviar email
                result = self.send_email(
                    to=notification['destinatario'],
                    subject=notification['assunto'],
                    body=notification['mensagem']
                )

                # Marcar como enviado
                self.mark_notification_sent(
                    notification['id'],
                    success=result['success']
                )

                print(f"  ✓ Notificação {notification['id']} enviada com sucesso")

            except Exception as e:
                print(f"  ❌ Erro ao enviar notificação {notification['id']}: {e}")
                self.mark_notification_sent(
                    notification['id'],
                    success=False,
                    error=str(e)
                )

    def run_continuous(self, interval: int = 60):
        """
        Executa o serviço continuamente

        Args:
            interval: Intervalo entre verificações em segundos
        """
        import time

        print(f"📨 Serviço de Email iniciado (intervalo: {interval}s)")

        while True:
            try:
                self.process_notifications()
            except Exception as e:
                print(f"❌ Erro no processamento: {e}")

            time.sleep(interval)


if __name__ == "__main__":
    # Configuração do banco de dados
    db_config = {
        'host': 'localhost',
        'database': 'documentos_db',
        'user': 'postgres',
        'password': 'YOUR_PASSWORD_HERE'
    }

    # Criar e executar serviço
    service = EmailNotificationService(db_config)
    service.run_continuous(interval=30)
