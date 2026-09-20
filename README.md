# COSEG Mobilidade

Sistema acadêmico de gestão de mobilidade e reservas de veículos, desenvolvido em Python e Django. O projeto foi construído para centralizar o cadastro e a administração de veículos, motoristas e reservas, aplicando regras de negócio para disponibilidade, capacidade, datas e conflitos de horários.

> Primeira entrega técnica do PBL 2 da disciplina de Programação para Web — Engenharia de Software, UNDB.

## Visão geral

Processos de reserva de veículos podem gerar conflitos de horário, alocação acima da capacidade, registros inconsistentes e perda de histórico quando não há uma gestão centralizada.

O **COSEG Mobilidade** é uma aplicação web que organiza esse processo. Nesta versão, o foco está no CRUD próprio de veículos e na base de domínio necessária para as próximas etapas de reservas e motoristas.

## Principais entregas

- CRUD de veículos fora do Django Admin:
  - Cadastro
  - Listagem
  - Pesquisa
  - Filtros
  - Paginação
  - Consulta de detalhes
  - Edição
  - Desativação e reativação
  - Exclusão protegida
- Modelagem de dados para `Veiculo`, `Motorista` e `Reserva`
- Regras de negócio implementadas no domínio da aplicação
- Login e permissões por operação
- Formulários protegidos com CSRF, validação por campo e mensagens de sucesso
- Interface responsiva com HTML semântico, Tailwind CSS e JavaScript
- Administração dos três modelos pelo Django Admin
- 50 testes automatizados de models, forms, views, permissões e integração
- Comando opcional para popular uma frota didática com 8 veículos leves e 2 coletivos

## Tecnologias

- Python 3.12+
- Django 6.1.1
- Django ORM
- SQLite
- HTML5
- Tailwind CSS 4
- JavaScript
- Git e GitHub
- Django Test Framework

## Arquitetura e organização

```text
setup/
├── setup/                         # Configurações e rotas principais do Django
├── reservas/
│   ├── models.py                  # Entidades e regras de negócio
│   ├── forms.py                   # ModelForm de veículo e formulário de login
│   ├── views.py                   # CRUD de veículos
│   ├── tests.py                   # Testes automatizados
│   ├── templates/                 # Páginas da aplicação
│   └── static/reservas/           # CSS, JavaScript e ícones
├── manage.py
├── package.json                   # Comandos e versão do Tailwind CSS
└── requirements.txt

docs/
├── IMPLEMENTACAO.md               # Explicação da adaptação técnica
├── CHECKLIST_PBL2.md              # Próximas etapas do PBL 2
└── README_PBL1_ORIGINAL.md        # README original preservado
```

## Funcionalidades implementadas

### Gestão de veículos

A aplicação permite administrar veículos por uma interface própria, sem depender exclusivamente do Django Admin.

- Criar, consultar, editar e excluir veículos
- Pesquisar por código ou informações do veículo
- Filtrar e paginar resultados
- Desativar e reativar veículos sem apagar o histórico
- Excluir definitivamente apenas veículos sem reservas vinculadas
- Exibir botões e ações conforme a permissão do usuário

### Autenticação e permissões

O sistema utiliza autenticação nativa do Django.

- Login e logout
- Controle de acesso por permissões do Django
- Proteção de rotas no servidor
- Ocultação de ações não permitidas na interface
- Proteção CSRF em formulários e operações sensíveis
- Confirmação explícita para desativação e exclusão

A interface própria não exige que o usuário tenha `is_staff`. O Django Admin exige usuário da equipe e permissões compatíveis com cada model.

### Qualidade e testes

O projeto possui 50 testes automatizados cobrindo:

- Models
- Forms
- Views
- Permissões
- Integrações
- Fluxos de CRUD
- Regras de negócio
- Proteções de exclusão e desativação

## Regras de negócio

As regras abaixo são aplicadas pelo backend. O JavaScript melhora a experiência da interface, mas não substitui a validação no servidor.

### Veículos

- Veículos leves possuem capacidade de 4 passageiros.
- Veículos coletivos possuem capacidade de 18 passageiros.
- A capacidade é calculada pelo model e não é aceita diretamente do navegador.
- O código do veículo deve ser único.
- Códigos são salvos em letras maiúsculas e sem espaços nas extremidades.
- Veículos podem ser desativados sem apagar o histórico.
- Veículos com reservas vinculadas não podem ser excluídos.
- A categoria de veículo com reservas não pode ser alterada, preservando a interpretação do histórico.
- Veículos com reservas em andamento ou futuras não podem ser desativados até que as reservas sejam realocadas.

### Reservas

- A quantidade de passageiros deve estar entre 1 e 18.
- Uma nova reserva não pode utilizar uma data passada.
- O horário de retorno deve ser posterior ao horário de saída no mesmo dia.
- Não pode haver sobreposição de reserva para o mesmo veículo.
- Não pode haver sobreposição de reserva para o mesmo motorista.
- Intervalos adjacentes são permitidos.
- Veículos e motoristas inativos não podem receber novas reservas.
- A categoria pretendida é uma preferência; a capacidade do veículo efetivamente alocado determina a adequação.
- Reservas passadas podem ter dados descritivos corrigidos, mas não permitem alteração de data, horários, quantidade de passageiros ou alocação.

## Rotas implementadas

| Rota | Função |
|---|---|
| `/` | Redireciona para a lista de veículos |
| `/veiculos/` | Lista, pesquisa, filtros e paginação |
| `/veiculos/novo/` | Cadastro de veículo |
| `/veiculos/<id>/` | Detalhes do veículo |
| `/veiculos/<id>/editar/` | Edição e reativação |
| `/veiculos/<id>/desativar/` | Confirmação e desativação por `POST` |
| `/veiculos/<id>/excluir/` | Confirmação e exclusão protegida por `POST` |
| `/contas/entrar/` | Login |
| `/contas/sair/` | Logout por `POST` |
| `/admin/` | Administração dos models |

Todas as rotas de veículos utilizam o namespace `reservas`.

Exemplo:

```python
reservas:veiculo_lista
```

## Permissões necessárias

O superusuário possui acesso completo.

Para usuários comuns, configure permissões no Django Admin por meio de **Usuários** ou **Grupos**.

| Permissão | Ação permitida |
|---|---|
| `view_veiculo` | Consultar veículos |
| `view_veiculo` + `add_veiculo` | Cadastrar veículos |
| `view_veiculo` + `change_veiculo` | Editar, desativar e reativar veículos |
| `view_veiculo` + `delete_veiculo` | Excluir veículos sem reservas vinculadas |

## Como executar localmente

### Pré-requisitos

- Python 3.12 ou superior
- Git
- PowerShell, terminal Linux ou macOS
- Node.js é opcional; necessário apenas para alterar ou recompilar os estilos Tailwind CSS

O projeto foi validado com:

```text
Python 3.12
Django 6.1.1
```

### 1. Clone o repositório

```bash
git clone [https://github.com/diegovitor90/conseg-mobilidade.git](https://github.com/diegovitor90/conseg-mobilidade.git)
cd conseg-mobilidade
```

### 2. Entre na pasta do projeto Django

```bash
cd setup
```

### 3. Crie e ative o ambiente virtual

#### Windows — PowerShell

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
```

#### Linux ou macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Instale as dependências

```bash
python -m pip install -r requirements.txt
```

### 5. Execute as migrations

```bash
python manage.py migrate
```

### 6. Crie um superusuário

```bash
python manage.py createsuperuser
```

Escolha seu próprio usuário e senha. O repositório não contém contas pré-criadas, banco com dados pessoais ou credenciais reais.

### 7. Popule a frota didática opcionalmente

```bash
python manage.py popular_frota
```

Esse comando cria 8 veículos leves e 2 veículos coletivos para demonstração. Ele pode ser executado novamente sem alterar veículos já existentes.

### 8. Inicie a aplicação

```bash
python manage.py runserver
```

Acesse:

- Aplicação: [http://127.0.0.1:8000/veiculos/](http://127.0.0.1:8000/veiculos/)
- Login: [http://127.0.0.1:8000/contas/entrar/](http://127.0.0.1:8000/contas/entrar/)
- Administração: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

### Alternativa se o PowerShell bloquear a ativação

Não é necessário alterar a política de execução. Use diretamente o Python do ambiente virtual:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py createsuperuser
.\venv\Scripts\python.exe manage.py popular_frota
.\venv\Scripts\python.exe manage.py runserver
```

## Tailwind CSS

O CSS já está compilado em `app.css`. Portanto, Node.js não é necessário para executar a aplicação.

Use Node.js somente se precisar alterar ou recompilar os estilos:

```bash
npm install
npm run build:css
```

Durante ajustes visuais:

```bash
npm run watch:css
```

## Como testar

Dentro da pasta `setup/`, com o ambiente virtual ativado:

```bash
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test reservas
```

As migrations necessárias estão incluídas. Em uma instalação nova, execute apenas:

```bash
python manage.py migrate
```

Não é necessário recriar migrations existentes.

## Limitações atuais e próximos passos

Esta é uma aplicação acadêmica para execução local e representa a primeira entrega técnica do PBL 2.

Ainda não estão concluídos:

- CRUD próprio de reservas
- CRUD próprio de motoristas
- API JSON
- Board final do projeto
- Apresentação final
- Deploy em ambiente de produção

### Considerações para produção

Antes de uso operacional em produção, seria necessário implementar e validar:

- Banco de dados gerenciado, como PostgreSQL
- Variáveis de ambiente e chave secreta exclusiva
- `DEBUG = False`
- HTTPS
- Estratégia de backup
- Proteção contra tentativas repetidas de login
- Observabilidade e logs
- Estratégia de concorrência e transações para evitar corridas entre reservas simultâneas
- Testes de carga e concorrência

As validações de conflito são seguras no fluxo sequencial atual. Porém, esta versão não promete impedir conflitos quando múltiplos processos criam reservas simultaneamente. Para esse cenário, seriam necessários mecanismos adequados de transação e bloqueio, conforme o banco de dados escolhido.

Também evite criar ou alterar reservas usando:

```python
QuerySet.update()
bulk_create()
SQL direto
```

Essas abordagens não executam `save()` ou `full_clean()` e podem contornar regras implementadas no domínio.

## Contexto acadêmico

**Autor:** Diego Vitor Lopes Gonçalves Souza  
**Curso:** Engenharia de Software — 5º período  
**Instituição:** Universidade Dom Bosco — UNDB  
**Disciplina:** Programação para Web  
**Professor:** Danilo Costa  
**Período:** 2026.2

## Aprendizados

Neste projeto, apliquei e aprofundei conhecimentos em:

- Desenvolvimento backend com Python e Django
- Modelagem de dados e Django ORM
- Operações CRUD
- Validações no frontend e no backend
- Regras de negócio
- Autenticação e autorização
- Controle de permissões
- Segurança com CSRF e operações `POST`
- Testes automatizados
- Interface responsiva com Tailwind CSS
- Documentação técnica e organização de projetoProgramação para Web · Prof. Danilo Costa · 2026.2
