"""
API Server - Backend REST API para o sistema de Achados e Perdidos
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from datetime import datetime
from typing import Dict, Optional
import os

app = Flask(__name__)
CORS(app)  # Permitir requisições do frontend

# Configuração do banco de dados
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'documentos_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'YOUR_PASSWORD_HERE')
}


def get_db_connection():
    """Cria conexão com o banco de dados"""
    return psycopg2.connect(**DB_CONFIG)


# ==================== ENDPOINTS DE USUÁRIOS ====================

@app.route('/api/usuarios', methods=['POST'])
def criar_usuario():
    """Cria novo usuário"""
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO usuarios (nome, email, telefone)
            VALUES (%s, %s, %s)
            RETURNING id, nome, email, criado_em
        """, (data['nome'], data['email'], data.get('telefone')))

        user = cursor.fetchone()
        conn.commit()

        return jsonify({
            'success': True,
            'usuario': {
                'id': user[0],
                'nome': user[1],
                'email': user[2],
                'criado_em': user[3].isoformat()
            }
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

    finally:
        cursor.close()
        conn.close()


# ==================== ENDPOINTS DE DOCUMENTOS PERDIDOS ====================

@app.route('/api/documentos-perdidos', methods=['POST'])
def registrar_documento_perdido():
    """Registra um documento perdido"""
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Buscar ou criar usuário
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (data['email'],))
        user = cursor.fetchone()

        if not user:
            cursor.execute("""
                INSERT INTO usuarios (nome, email)
                VALUES (%s, %s)
                RETURNING id
            """, (data.get('nome_documento', 'Usuário'), data['email']))
            usuario_id = cursor.fetchone()[0]
        else:
            usuario_id = user[0]

        # Inserir documento perdido
        cursor.execute("""
            INSERT INTO documentos_perdidos
            (usuario_id, tipo_documento, numero_documento, nome_documento,
             cpf_documento, descricao)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, criado_em
        """, (
            usuario_id,
            data['tipo_documento'],
            data.get('numero_documento'),
            data.get('nome_documento'),
            data.get('cpf_documento'),
            data.get('descricao')
        ))

        doc_id, criado_em = cursor.fetchone()
        conn.commit()

        return jsonify({
            'success': True,
            'documento_id': doc_id,
            'usuario_id': usuario_id,
            'criado_em': criado_em.isoformat(),
            'mensagem': 'Documento perdido registrado com sucesso!'
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

    finally:
        cursor.close()
        conn.close()


@app.route('/api/documentos-perdidos', methods=['GET'])
def listar_documentos_perdidos():
    """Lista documentos perdidos"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT dp.id, dp.tipo_documento, dp.numero_documento,
                   dp.nome_documento, dp.status, dp.criado_em,
                   u.email
            FROM documentos_perdidos dp
            JOIN usuarios u ON dp.usuario_id = u.id
            WHERE dp.status = 'perdido'
            ORDER BY dp.criado_em DESC
        """)

        documentos = []
        for row in cursor.fetchall():
            documentos.append({
                'id': row[0],
                'tipo_documento': row[1],
                'numero_documento': row[2],
                'nome_documento': row[3],
                'status': row[4],
                'criado_em': row[5].isoformat(),
                'email': row[6]
            })

        return jsonify({'success': True, 'documentos': documentos})

    finally:
        cursor.close()
        conn.close()


# ==================== ENDPOINTS DE DOCUMENTOS ACHADOS ====================

@app.route('/api/documentos-achados', methods=['POST'])
def registrar_documento_achado():
    """Registra um documento achado"""
    data = request.json

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Buscar ou criar usuário
        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (data['email'],))
        user = cursor.fetchone()

        if not user:
            cursor.execute("""
                INSERT INTO usuarios (nome, email)
                VALUES (%s, %s)
                RETURNING id
            """, (data.get('nome_documento', 'Encontrador'), data['email']))
            encontrador_id = cursor.fetchone()[0]
        else:
            encontrador_id = user[0]

        # Inserir documento achado
        cursor.execute("""
            INSERT INTO documentos_achados
            (encontrador_id, tipo_documento, numero_documento, nome_documento,
             cpf_documento, local_encontrado, latitude, longitude, descricao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id, criado_em
        """, (
            encontrador_id,
            data['tipo_documento'],
            data.get('numero_documento'),
            data.get('nome_documento'),
            data.get('cpf_documento'),
            data['local_encontrado'],
            data['latitude'],
            data['longitude'],
            data.get('descricao')
        ))

        doc_id, criado_em = cursor.fetchone()
        conn.commit()

        return jsonify({
            'success': True,
            'documento_id': doc_id,
            'encontrador_id': encontrador_id,
            'criado_em': criado_em.isoformat(),
            'mensagem': 'Documento achado registrado com sucesso!'
        }), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

    finally:
        cursor.close()
        conn.close()


@app.route('/api/documentos-achados', methods=['GET'])
def listar_documentos_achados():
    """Lista documentos achados"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT id, tipo_documento, numero_documento, nome_documento,
                   local_encontrado, latitude, longitude, status, criado_em
            FROM documentos_achados
            WHERE status = 'disponivel'
            ORDER BY criado_em DESC
        """)

        documentos = []
        for row in cursor.fetchall():
            documentos.append({
                'id': row[0],
                'tipo_documento': row[1],
                'numero_documento': row[2],
                'nome_documento': row[3],
                'local_encontrado': row[4],
                'latitude': float(row[5]) if row[5] else None,
                'longitude': float(row[6]) if row[6] else None,
                'status': row[7],
                'criado_em': row[8].isoformat()
            })

        return jsonify({'success': True, 'documentos': documentos})

    finally:
        cursor.close()
        conn.close()


# ==================== ENDPOINTS DE MATCHES ====================

@app.route('/api/matches', methods=['GET'])
def listar_matches():
    """Lista matches encontrados"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT m.id, m.score_similaridade, m.status, m.criado_em,
                   dp.tipo_documento, dp.nome_documento, dp.numero_documento,
                   da.local_encontrado, da.latitude, da.longitude,
                   u.email, u.nome
            FROM matches m
            JOIN documentos_perdidos dp ON m.documento_perdido_id = dp.id
            JOIN documentos_achados da ON m.documento_achado_id = da.id
            JOIN usuarios u ON dp.usuario_id = u.id
            ORDER BY m.criado_em DESC
        """)

        matches = []
        for row in cursor.fetchall():
            matches.append({
                'id': row[0],
                'score': float(row[1]),
                'status': row[2],
                'criado_em': row[3].isoformat(),
                'tipo_documento': row[4],
                'nome_documento': row[5],
                'numero_documento': row[6],
                'local_encontrado': row[7],
                'latitude': float(row[8]) if row[8] else None,
                'longitude': float(row[9]) if row[9] else None,
                'email_dono': row[10],
                'nome_dono': row[11]
            })

        return jsonify({'success': True, 'matches': matches})

    finally:
        cursor.close()
        conn.close()


# ==================== ENDPOINT DE ESTATÍSTICAS ====================

@app.route('/api/estatisticas', methods=['GET'])
def obter_estatisticas():
    """Retorna estatísticas do sistema"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Contar documentos perdidos
        cursor.execute("SELECT COUNT(*) FROM documentos_perdidos WHERE status = 'perdido'")
        total_perdidos = cursor.fetchone()[0]

        # Contar documentos achados
        cursor.execute("SELECT COUNT(*) FROM documentos_achados WHERE status = 'disponivel'")
        total_achados = cursor.fetchone()[0]

        # Contar matches
        cursor.execute("SELECT COUNT(*) FROM matches")
        total_matches = cursor.fetchone()[0]

        # Contar recuperações
        cursor.execute("SELECT COUNT(*) FROM documentos_perdidos WHERE status = 'encontrado'")
        total_recuperados = cursor.fetchone()[0]

        return jsonify({
            'success': True,
            'estatisticas': {
                'documentos_perdidos': total_perdidos,
                'documentos_achados': total_achados,
                'matches': total_matches,
                'recuperados': total_recuperados
            }
        })

    finally:
        cursor.close()
        conn.close()


# ==================== HEALTH CHECK ====================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Verifica se a API está funcionando"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("🚀 Iniciando servidor API...")
    print("📍 Disponível em: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
