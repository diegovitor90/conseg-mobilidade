# COSEG Mobilidade

Backend para gerenciamento de reservas de veículos do setor COSEG do Porto do Itaqui.

O projeto está sendo desenvolvido no PBL 1 da disciplina **Programação para Web**, do 5º período de Engenharia de Software da UNDB. Nesta primeira etapa, o foco é construir a camada de servidor em Python e Django, centralizando os dados e as regras de negócio das reservas.

## Problema

Atualmente, as solicitações de transporte chegam ao COSEG por diferentes canais, como ligações, mensagens, e-mails e planilhas. A falta de um registro centralizado pode provocar:

- reservas conflitantes para o mesmo veículo;
- escolha de veículos com capacidade insuficiente;
- desconsideração do horário de retorno;
- orientações contraditórias aos motoristas;
- atrasos e retrabalho entre os setores.

O COSEG Mobilidade propõe centralizar veículos, motoristas e reservas em um banco de dados, facilitando a consulta da frota e evitando conflitos de utilização.

## Objetivo

Desenvolver um backend em Django capaz de cadastrar, consultar, atualizar e excluir veículos, motoristas e reservas, aplicando as regras de negócio definidas no problema.

## Tecnologias

- Python 3;
- Django;
- Django ORM;
- SQLite;
- HTML e CSS, nas interfaces do CRUD;
- Git e GitHub, para versionamento.

## Funcionalidades previstas

- CRUD de veículos;
- CRUD de motoristas;
- CRUD de reservas;
- administração dos registros pelo Django Admin;
- persistência dos dados no SQLite;
- seleção da categoria de veículo adequada;
- vinculação posterior de um veículo e de um motorista à reserva;
- validação da capacidade do veículo;
- validação da data e dos horários da reserva;
- prevenção de conflitos de veículos e motoristas.

## Regras de negócio

1. Veículos leves transportam no máximo 4 passageiros.
2. Veículos coletivos transportam no máximo 18 passageiros.
3. Solicitações com mais de 18 passageiros devem ser rejeitadas.
4. A quantidade de passageiros deve ser maior que zero.
5. A data de uma nova reserva não pode estar no passado.
6. O horário de retorno deve ser posterior ao horário de saída.
7. A quantidade de passageiros não pode ultrapassar a capacidade do veículo escolhido.
8. Um veículo não pode ser reservado para intervalos de tempo sobrepostos.
9. Um motorista não pode ser atribuído a reservas com horários sobrepostos.
10. Uma nova reserva pode começar exatamente no horário em que a reserva anterior termina.

## Models

### Veiculo

Representa os veículos da frota do COSEG.

Campos principais:

- código;
- categoria: leve ou coletivo;
- capacidade;
- ativo;
- data de criação;
- data de atualização.

### Motorista

Representa os profissionais responsáveis pelos deslocamentos.

Campos principais:

- nome;
- matrícula;
- CNH;
- ativo;
- data de criação;
- data de atualização.

### Reserva

Representa uma solicitação de transporte.

Campos principais:

- solicitante;
- setor;
- atividade;
- origem;
- destino;
- data;
- horário de saída;
- horário de retorno;
- quantidade de passageiros;
- categoria pretendida;
- veículo;
- motorista;
- observações;
- data de criação;
- data de atualização.

O veículo e o motorista podem ser opcionais no momento da solicitação e selecionados posteriormente pelo profissional do COSEG.

## Relacionamentos

```text
Veiculo   1 ───── N Reserva
Motorista 1 ───── N Reserva
```

Um veículo e um motorista podem participar de várias reservas, desde que não existam conflitos de horário. Cada reserva pode possuir um veículo e um motorista.

## Estrutura esperada

```text
COSEG-Mobilidade/
├── core/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── reservas/
│   ├── migrations/
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── templates/
│   └── reservas/
├── db.sqlite3
├── manage.py
├── requirements.txt
└── README.md
```

## Como executar o projeto

### 1. Entrar na pasta do projeto

```powershell
cd "caminho\para\COSEG-Mobilidade"
```

### 2. Criar o ambiente virtual

```powershell
py -m venv venv
```

### 3. Ativar o ambiente virtual

No PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Caso a pasta do ambiente virtual já exista, não é necessário criá-la novamente.

### 4. Instalar as dependências

```powershell
pip install -r requirements.txt
```

Se o arquivo `requirements.txt` ainda não existir:

```powershell
pip install django
pip freeze > requirements.txt
```

### 5. Criar e aplicar as migrations

```powershell
py manage.py makemigrations
py manage.py migrate
```

### 6. Criar o administrador

```powershell
py manage.py createsuperuser
```

### 7. Executar o servidor

```powershell
py manage.py runserver
```

Aplicação local:

```text
http://127.0.0.1:8000/
```

Django Admin:

```text
http://127.0.0.1:8000/admin/
```

## Operações CRUD

CRUD é o conjunto das quatro operações fundamentais realizadas sobre os dados:

- **Create:** cadastrar um registro;
- **Read:** consultar ou listar registros;
- **Update:** alterar um registro;
- **Delete:** excluir um registro.

O Django Admin permite testar essas operações inicialmente. O CRUD próprio da aplicação será implementado posteriormente por meio de forms, views, URLs e templates.

## Rotas planejadas

```text
/veiculos/
/veiculos/novo/
/veiculos/<id>/editar/
/veiculos/<id>/excluir/

/motoristas/
/motoristas/novo/
/motoristas/<id>/editar/
/motoristas/<id>/excluir/

/reservas/
/reservas/nova/
/reservas/<id>/editar/
/reservas/<id>/excluir/
```

## Testes planejados

Os testes automatizados deverão verificar, pelo menos:

- rejeição de reservas com mais de 18 passageiros;
- rejeição de datas no passado;
- rejeição de retorno igual ou anterior à saída;
- rejeição de quantidade superior à capacidade do veículo;
- rejeição de conflito de horário do veículo;
- rejeição de conflito de horário do motorista;
- aceitação de uma reserva que começa quando a anterior termina.

## Acompanhamento do desenvolvimento

- [x] Criação do ambiente virtual;
- [x] Instalação do Django;
- [x] Criação do projeto `core`;
- [x] Configuração inicial do SQLite;
- [x] Execução das migrations iniciais;
- [x] Inicialização do servidor de desenvolvimento;
- [ ] Criação e revisão do app `reservas`;
- [ ] Criação dos models `Veiculo`, `Motorista` e `Reserva`;
- [ ] Registro dos models no Django Admin;
- [ ] Implementação completa das validações;
- [ ] Implementação das views e rotas do CRUD;
- [ ] Criação dos formulários e templates;
- [ ] Criação dos testes automatizados;
- [ ] Revisão da documentação e apresentação final.

Marque um item com `[x]` somente depois de confirmar que ele está funcionando no projeto.

## Autor

**Diego Vitor Lopes Gonçalves Souza**  
Engenharia de Software — 5º período — UNDB

## Informações acadêmicas

- **Disciplina:** Programação para Web;
- **Professor:** Danilo Costa;
- **Projeto:** PBL 1 — Agenda em Conflito: Sistema COSEG de Reserva de Veículos do Porto do Itaqui;
- **Semestre:** 2026.2.

## Status

Projeto acadêmico em desenvolvimento.
