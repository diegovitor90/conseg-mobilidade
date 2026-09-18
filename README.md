# COSEG Mobilidade

Primeira entrega técnica do PBL 2: CRUD próprio de veículos dentro do app `reservas`, com interface responsiva e integração ao Django.

## O que veio no ZIP e o que foi feito

O ZIP recebido continha somente o projeto inicial em `setup/`, além de dois ambientes virtuais Windows. Não continha o app `reservas`, migrations próprias ou banco SQLite. O Board e o README descreviam os models, mas esses arquivos ainda não estavam no pacote.

Esta versão preserva o nome **setup** e o ponto de entrada `manage.py`. Acrescenta os models descritos nos documentos e adapta o padrão de CRUD de veículos do projeto [Oficina Web](https://github.com/diegovitor90/oficina-web), revisão `d4e3cef2e3bb5b03fa661cd2f1d701897af59555`. Nenhum app da Oficina foi simplesmente renomeado.

O README original recebido foi preservado em `docs/README_PBL1_ORIGINAL.md`. O Board e os slides enviados não foram alterados.

**Atenção:** se a versão no seu computador já tiver models, banco ou migrations que não vieram neste ZIP, não substitua esses arquivos diretamente. Compare as versões antes de integrar. Não apague migrations nem seu banco.

## O que está pronto

- Models `Veiculo`, `Motorista` e `Reserva`, com migration inicial.
- CRUD de veículos fora do Admin: cadastrar, listar, pesquisar, filtrar, paginar, consultar, editar e excluir.
- Desativação e reativação sem apagar histórico.
- Exclusão real apenas para veículos sem reservas vinculadas.
- Login e permissões por operação, usando as contas do próprio Django.
- Formulários com CSRF, erros por campo e mensagens de sucesso.
- HTML semântico, Tailwind CSS 4 compilado localmente e JavaScript para responsividade e previsão da capacidade.
- Admin para veículos, motoristas e reservas.
- 50 testes automatizados de models, forms, views, permissões e integração.
- Comando opcional de frota didática: 8 veículos leves e 2 coletivos.

**Esta entrega não encerra o PBL 2.** Os CRUDs próprios de reservas e motoristas, API JSON, Board final e apresentação permanecem como próximas etapas. Reservas e motoristas são gerenciados pelo Admin nesta versão. Não houve publicação nem alteração no GitHub.

## Executar no Windows

Requer **Python 3.12 ou superior**. Validado com Python 3.12 e Django 6.1.1. O ambiente virtual deve ser criado novamente no computador de quem executa.

1. Extraia o ZIP em uma pasta separada.
2. Abra o terminal na pasta `undb_desenvolvimento_web`.
3. Execute:

```powershell
cd setup
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py popular_frota
python manage.py runserver
```

O comando `popular_frota` é opcional. Ele cria dados didáticos e pode ser executado novamente: não altera veículos que já existem.

Escolha seu próprio usuário e senha em `createsuperuser`. O pacote **não contém contas pré-criadas nem banco com dados pessoais**. As credenciais fictícias em `tests.py` existem apenas no banco temporário dos testes.

Se o PowerShell bloquear a ativação, não é necessário mudar a política de execução. Use o Python do ambiente diretamente:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
.\venv\Scripts\python.exe manage.py migrate
.\venv\Scripts\python.exe manage.py createsuperuser
.\venv\Scripts\python.exe manage.py popular_frota
.\venv\Scripts\python.exe manage.py runserver
```

- Aplicação: [localhost:8000/veiculos/](http://127.0.0.1:8000/veiculos/)
- Login: [localhost:8000/contas/entrar/](http://127.0.0.1:8000/contas/entrar/)
- Admin: [localhost:8000/admin/](http://127.0.0.1:8000/admin/)

No Linux/macOS, troque `py` por `python3` para criar o ambiente e ative com `source venv/bin/activate`.

O CSS do Tailwind já está compilado em `app.css`. Portanto, **Node.js não é necessário para executar o sistema**. Ele só é necessário para alterar ou recompilar os estilos:

```powershell
npm install
npm run build:css
```

Durante a edição visual, use `npm run watch:css` para recompilar automaticamente.

## Testar

Na pasta `setup/`, com o ambiente ativado:

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test reservas
```

As migrations necessárias estão incluídas. Em uma instalação nova, use `migrate`; não é preciso recriá-las.

## Rotas implementadas

| Rota | Função |
| --- | --- |
| `/` | Redireciona para veículos |
| `/veiculos/` | Lista, pesquisa, filtros e paginação |
| `/veiculos/novo/` | Cadastro |
| `/veiculos/<id>/` | Detalhes |
| `/veiculos/<id>/editar/` | Edição e reativação |
| `/veiculos/<id>/desativar/` | Confirmação e desativação por POST |
| `/veiculos/<id>/excluir/` | Confirmação e exclusão protegida por POST |
| `/contas/entrar/` | Login |
| `/contas/sair/` | Logout por POST |
| `/admin/` | Administração dos três models |

Todas as rotas de veículos usam o namespace `reservas`. Exemplo: `reservas:veiculo_lista`.

## Permissões

O superusuário tem acesso completo. Para uma conta comum, conceda as permissões em Usuários ou Grupos no Admin:

- `view_veiculo`: consultar.
- `view_veiculo` + `add_veiculo`: cadastrar.
- `view_veiculo` + `change_veiculo`: editar, desativar e reativar.
- `view_veiculo` + `delete_veiculo`: excluir quando não há reservas.

A interface própria não exige `is_staff`. O Admin exige usuário da equipe e as permissões dos respectivos models. Os botões são ocultados conforme a permissão, mas o bloqueio também ocorre no servidor.

## Regras de negócio

- Leve: 4 passageiros. Coletivo: 18. A capacidade é calculada pelo model, nunca aceita do navegador.
- Código de veículo único, sem espaços nas extremidades e salvo em maiúsculas.
- Quantidade de passageiros entre 1 e 18.
- Nova reserva não pode ter data no passado.
- Retorno posterior à saída, no mesmo dia.
- Veículo e motorista podem ser escolhidos depois, conforme o README do PBL 1.
- Sem sobreposição de veículo ou de motorista: intervalos adjacentes são permitidos.
- Recursos inativos não recebem novas reservas.
- Categoria pretendida é uma preferência; a capacidade do veículo efetivamente alocado determina a adequação.
- Reservas passadas permitem corrigir dados descritivos, mas não data, horários, passageiros ou alocação.

Decisões de proteção acrescentadas nesta adaptação:

- `PROTECT` impede apagar veículos ou motoristas com reservas.
- Categoria de um veículo com reservas não pode ser alterada, preservando a interpretação do histórico.
- Desativar veículo ou motorista com reservas em andamento/futuras é bloqueado. Realoque as reservas antes.
- Exclusões exigem POST, CSRF, permissão e confirmação explícita.

## Limites desta versão

Aplicação acadêmica para execução local, sem configuração de produção. O JavaScript melhora o feedback, mas o servidor continua validando.

As consultas de conflito são validadas no fluxo sequencial. Esta versão **não promete impedir corridas entre reservas simultâneas em múltiplos processos**. Antes de uso operacional, definir transações/bloqueios adequados e testar concorrência com o banco escolhido.

`QuerySet.update()`, `bulk_create()` e SQL direto não executam `save()/full_clean()`. Não os use para criar/alterar reservas. As constraints incluídas protegem limites simples no banco, mas não toda regra entre registros.

O fuso horário é `America/Fortaleza`. Para produção: chave secreta própria, DEBUG desligado, HTTPS, proteção contra tentativas repetidas de login, backups e estratégia de concorrência, entre outros controles.

## Organização

- `setup/setup/`: configurações e rotas principais.
- `setup/reservas/models.py`: regras e entidades.
- `setup/reservas/forms.py`: ModelForm de veículo e formulário de login.
- `setup/reservas/views.py`: CRUD de veículos.
- `setup/reservas/templates/`: páginas próprias.
- `setup/reservas/static/reservas/`: Tailwind compilado, arquivo-fonte CSS, JavaScript e ícone.
- `setup/package.json`: comandos e versão do Tailwind CSS usados no projeto.
- `setup/reservas/tests.py`: testes automatizados.
- `docs/IMPLEMENTACAO.md`: explicação da adaptação.
- `docs/CHECKLIST_PBL2.md`: o que falta para as etapas seguintes.

## Autoria e contexto

Diego Vitor Lopes Gonçalves Souza  
Engenharia de Software, 5º período, UNDB  
Programação para Web · Prof. Danilo Costa · 2026.2
