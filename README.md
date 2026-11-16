# AgendaBella

Agenda online para pequenos salões de beleza de bairro. MVP desenvolvido na disciplina de **Projeto de Software** (Experiências Práticas I, II e III), a partir do diagnóstico do parceiro comunitário **Studio Bella Cabelos** (Méier, Rio de Janeiro/RJ).

## Problema

O salão gerencia agendamentos de forma manual (WhatsApp, telefone e agenda de papel), o que gera horários duplicados, cerca de 6 faltas por semana sem aviso e interrupções constantes nos atendimentos.

## Solução (MVP)

- A cliente agenda sozinha por um link, escolhendo serviço, profissional, dia e um horário **realmente livre**.
- O sistema **impede conflitos de horário** (validação na camada de serviço e restrição no banco).
- A equipe acessa um **painel** autenticado com a agenda do dia/semana e marca atendimentos como realizado, falta ou cancelado.

ODS relacionado: **ODS 8 — Trabalho Decente e Crescimento Econômico** (metas 8.2 e 8.3).

## Arquitetura

Cliente-servidor com back-end monolítico em camadas:

```
frontend/  Angular (SPA + PWA) — telas da cliente e painel da equipe
backend/   Python 3.12 + FastAPI
           ├── routers/      controladores REST (validação de entrada e autenticação)
           ├── services/     regras de negócio (horários livres, conflitos, autenticação)
           ├── repositories  acesso a dados com SQLAlchemy (consultas parametrizadas)
           └── models        entidades Profissional, Cliente, Servico, Agendamento
```

Banco de dados: PostgreSQL em produção e SQLite em desenvolvimento/testes.

## Requisitos implementados

| ID | Prioridade | Descrição |
|----|-----------|-----------|
| RF01 | Obrigatório | Exibir horários disponíveis por serviço, profissional e data |
| RF02 | Obrigatório | Registrar agendamento impedindo sobreposição de horários |
| RF03 | Obrigatório | Login da equipe com e-mail e senha (Argon2id + JWT) |
| RF04 | Obrigatório | Painel com agenda do dia e da semana por profissional |
| RF05 | Obrigatório | Alterar status do agendamento (realizado, falta, cancelado) |

## Como executar

### Back-end

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
python -m app.seed          # cria o banco local com dados fictícios
uvicorn app.main:app --reload
```

A documentação interativa da API fica em `http://localhost:8000/docs` (desabilitada em produção).

### Testes

```bash
cd backend
pytest --cov=app --cov-report=term-missing
```

### Front-end

```bash
cd frontend
npm ci
npm start                   # http://localhost:4200
```

## Variáveis de ambiente (back-end)

| Variável | Descrição | Padrão (dev) |
|----------|-----------|--------------|
| `DATABASE_URL` | String de conexão do banco | `sqlite:///./agendabella.db` |
| `JWT_SECRET` | Chave de assinatura dos tokens | valor de desenvolvimento |
| `CORS_ORIGINS` | Origens permitidas, separadas por vírgula | `http://localhost:4200` |
| `APP_ENV` | `development` ou `production` | `development` |

Nenhum segredo deve ser versionado; use variáveis de ambiente do provedor de hospedagem.

## Dados de demonstração

Todos os dados do seed são fictícios. Login de teste da equipe: `marcia@studiobella.test` / `senha-demo-123` (apenas ambiente local).

## Autor

Felipe Castro Sotto Mayor — Análise e Desenvolvimento de Sistemas, Instituto Infnet.
