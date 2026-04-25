Description

Agentapp que cria um sistema completo de documentos perdidos e achados com backend inteligente (agente de monitoramento automático), frontend com mapa interativo, sistema de notificação por email e matching automático de documentos

Agent logic

**Golden Path**: Este agentapp usa ferramentas padrão de escrita de arquivos (Write) e upload para S3. Nenhuma ferramenta falhou repetidamente na sessão original, portanto o caminho primário é direto.

**Workflow para criar Sistema de Achados e Perdidos**:

1. Criar estrutura de diretórios do projeto: criar pasta `backend/` e `frontend/`

2. Criar schema do banco de dados PostgreSQL (`database-schema.sql`) com:
   
   - Tabela `usuarios` (id, nome, email, telefone, criado_em)
   
   - Tabela `documentos_perdidos` (id, usuario_id, tipo_documento, numero_documento, nome_documento, cpf_documento, data_perda, local_perda, descricao, foto_url, status, criado_em, atualizado_em)
   
   - Tabela `documentos_achados` (id, encontrador_id, tipo_documento, numero_documento, nome_documento, cpf_documento, data_encontrado, local_encontrado, latitude, longitude, descricao, foto_url, status, criado_em, atualizado_em)
  
   - Tabela `matches` (id, documento_perdido_id, documento_achado_id, score_similaridade, notificacao_enviada, data_notificacao, status, criado_em)
   
   - Tabela `notificacoes` (id, match_id, usuario_id, tipo, destinatario, assunto, mensagem, enviado, data_envio, erro, criado_em)
   - Índices otimizados para tipo_documento, numero_documento, cpf_documento e status

3. Criar agente de monitoramento (`backend/matching_agent.py`) que:
   - Conecta ao PostgreSQL usando psycopg2
   
   - Roda em loop contínuo a cada 30 segundos (configurável)
   
   - Busca documentos perdidos com status='perdido' e achados com status='disponivel'
   
   - Calcula score de similaridade: tipo_documento (20%), numero_documento (40%), nome_documento (25%), cpf_documento (15%)
   
   - Cria match se score >= 60%
   
   - Gera notificação pendente com email formatado incluindo coordenadas GPS

4. Criar serviço de email (`backend/email_service.py`) que:
   
   - Processa notificações pendentes (enviado=FALSE)
   - Envia emails com informações do documento e localização
   - Marca notificações como enviadas
   - Integra com CREAO Gmail MCP usando mcp__creao_platform__call_creao_tool_function
   - Roda em loop contínuo a cada 30 segundos

5. Criar API REST (`backend/api_server.py`) com Flask e CORS:
   - POST /api/documentos-perdidos (registrar documento perdido)
   - GET /api/documentos-perdidos (listar perdidos)
   - POST /api/documentos-achados (registrar documento achado com latitude/longitude)
   - GET /api/documentos-achados (listar achados)
   - GET /api/matches (listar correspondências)
   - GET /api/estatisticas (contadores do sistema)
   - GET /api/health (health check)
   - Criar/buscar usuários automaticamente por email

6. Criar interface frontend (`frontend/index.html`) com:
   - Design moderno com gradientes (CSS3 Grid/Flexbox)
   - Header com título e estatísticas (3 cards: perdidos, achados, matches)
   - Formulário "Perdi um Documento": tipo, número, nome, CPF, email, descrição
   - Formulário "Achei um Documento": tipo, número, nome, CPF, email, local + mapa interativo
   - Mapa Leaflet com OpenStreetMap para marcar coordenadas (click to pin)
   - Seção "Correspondências Encontradas" mostrando matches com score e botão "Ver no Mapa"

7. Criar lógica JavaScript (`frontend/app.js`) que:
   - Inicializa mapa Leaflet centrado em São Paulo (-23.5505, -46.6333)
   - Captura cliques no mapa para salvar latitude/longitude
   - Processa formulários e salva em localStorage (demonstração)
   - Implementa algoritmo de matching similar ao backend
   - Calcula similaridade usando Levenshtein distance
   - Exibe matches encontrados com informações detalhadas
   - Função showOnMap() para visualizar localização no mapa

8. Criar arquivo de dependências (`backend/requirements.txt`):
   - flask==3.0.0
   - flask-cors==4.0.0
   - psycopg2-binary==2.9.9
   - python-dotenv==1.0.0

9. Criar documentação completa (`README.md`) incluindo:
   - Arquitetura do sistema (diagrama de componentes)
   - Estrutura de arquivos
   - Funcionalidades e diferenciais
   - Como funciona o matching (pesos e threshold)
   - Endpoints da API
   - Tecnologias utilizadas
   - Fluxo completo do sistema

10. Criar guia de instalação (`SETUP_GUIDE.md`) com:
    - Instalação do PostgreSQL
    - Criação do banco de dados
    - Instalação de dependências Python
    - Configuração de variáveis de ambiente (.env)
    - Como rodar os 3 serviços (API, Matching Agent, Email Service)
    - Como abrir o frontend
    - Testes do sistema completo
    - Troubleshooting

11. Usar Write tool para criar todos os arquivos localmente

12. Usar mcp__creao_platform__upload_file_to_s3 para fazer upload de todos os arquivos gerados

13. Usar mcp__creao_platform__report_task_result para reportar conclusão com lista de todos os arquivos criados

14. Usar mcp__creao_platform__recommend_user_followup_query para sugerir:
    - Hospedar frontend em servidor estático
    - Integrar Gmail MCP para emails reais
    - Expandir funcionalidades (upload de fotos, autenticação, etc.)

**IMPORTANTE**: Todos os arquivos devem usar caminhos absolutos começando com /home/user/workspaces/. O sistema NÃO é interativo - não pergunte nada ao usuário, execute diretamente todas as etapas.

-----------------------------------------------------------------------------------------------

