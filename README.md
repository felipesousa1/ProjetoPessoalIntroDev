# ProjetoPessoalIntroDev

Projeto desenvolvido para a disciplina MAC0350 por Felipe Sousa dos Santos (NUSP:12567141).

O FastCards é uma aplicação web de flashcards focada em repetição espaçada (Spaced Repetition). O objetivo é facilitar a memorização de conteúdos através da criação de decks e cards, onde o sistema agenda automaticamente as revisões baseando-se no desempenho do usuário.

### TECNOLOGIAS UTILIZADAS

* Back-end: Python com FastAPI.
* Banco de Dados: SQLite com SQLModel (ORM).
* Front-end: Jinja2 para templates e HTMX para interatividade e dinamismo nas páginas.
* Suporte de IA: Utilizei ferramentas de IA generativa como auxílio na estilização do CSS/HTML/HTMX e para agilizar o processo de debugging.

---

### COMO RODAR O PROJETO

O projeto utiliza um ambiente virtual para gerenciar as dependências. Siga os passos abaixo no terminal:

1. Clone o repositório e acesse o repositório do projeto.
2. Crie e ative o ambiente virtual:
  python -m venv .venv
  source .venv/bin/activate

3. Instale as dependências:
  touch requirements.txt
  echo fastapi[standard] > requirements.txt
  echo jinja2 >> requirements.txt 
  echo sqlmodel >> requirements.txt
  pip install -r requirements.txt

5. Inicie o servidor de desenvolvimento:
   fastapi dev

 O sistema estará disponível em: http://127.0.0.1:8000

---

### SUPORTE

Caso encontre algum bug ou tenha alguma dificuldade técnica para rodar a aplicação, por favor, abra uma "Issue" detalhando o problema.
