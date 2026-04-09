from fastapi import FastAPI, Request, Form, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from contextlib import asynccontextmanager
from models import Deck, Flashcard, create_db_and_tables, engine
from datetime import date, timedelta, datetime
from fastapi.staticfiles import StaticFiles

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield
    
app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

def get_session():
    with Session(engine) as session:
        yield session

@app.get("/", response_class=HTMLResponse)
def read_decks(request: Request, session: Session = Depends(get_session)):
    limit = 5
    statement = select(Deck).order_by(Deck.id.desc())
    
    total_decks = len(session.exec(statement).all())
    decks = session.exec(statement.limit(limit)).all()
    has_next = total_decks > limit
    total_pages = max(1, (total_decks + limit - 1) // limit)
    
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"decks": decks, "page": 1, "q": "", "has_next": has_next, "total_pages": total_pages}
    )

@app.post("/decks")
def create_deck(name: str = Form(...), session: Session = Depends(get_session)):
    existing_deck = session.exec(select(Deck).where(Deck.name == name)).first()
    if existing_deck:
        return HTMLResponse("<script>alert('Um deck com este nome já existe!'); window.history.back();</script>")
    
    new_deck = Deck(name=name)
    session.add(new_deck)
    session.commit()
    # volta para a página incial depois de criar novo deck
    return RedirectResponse(url="/", status_code=303)

@app.get("/decks/{deck_id}", response_class=HTMLResponse)
def read_deck(request: Request, deck_id: int, session: Session = Depends(get_session)):
    deck = session.get(Deck, deck_id)
    if not deck:
        return "Deck nao encontrado"
    
    statement = select(Flashcard).where(Flashcard.deck_id == deck_id).order_by(Flashcard.id.desc()).limit(5)
    flashcards = session.exec(statement).all()
    
    total_cards = len(session.exec(select(Flashcard).where(Flashcard.deck_id == deck_id)).all())
    has_next = total_cards > 5
    total_pages = max(1, (total_cards + 5 - 1) // 5)

    return templates.TemplateResponse(
        request=request, 
        name="deck.html", 
        context={
            "deck": deck, 
            "flashcards": flashcards, 
            "deck_id": deck_id, 
            "page": 1, 
            "q": "", 
            "has_next": has_next,
            "total_pages": total_pages
        }
    )
    
@app.post("/flashcards")
def create_flashcard(
    response: Response, 
    front: str = Form(...), 
    back: str = Form(...), 
    deck_id: int = Form(...), 
    session: Session = Depends(get_session)
):
    existing_card = session.exec(
        select(Flashcard).where(Flashcard.front == front, Flashcard.back == back, Flashcard.deck_id == deck_id)
    ).first()
    
    if existing_card:
        response.headers["HX-Trigger"] = "duplicate-flashcard"
        return ""
    
    flashcard = Flashcard(front=front, back=back, deck_id=deck_id)
    session.add(flashcard)
    session.commit()
    
    response.headers["HX-Trigger"] = "flashcards-changed"
    return ""

@app.get("/flashcards")
def read_flashcards(session: Session = Depends(get_session)):
    flashcards = session.exec(select(Flashcard)).all()
    return flashcards

@app.put("/flashcards/{flashcard_id}")
def update_flashcard(
    request: Request,
    flashcard_id: int, 
    front: str = Form(...), 
    back: str = Form(...), 
    session: Session = Depends(get_session)
):
    flashcard = session.get(Flashcard, flashcard_id)
    if not flashcard:
        return "Flashcard não encontrado"
    
    flashcard.front = front
    flashcard.back = back
    session.add(flashcard)
    session.commit()
    session.refresh(flashcard)
    return templates.TemplateResponse(request=request, name="flashcard.html", context={"card": flashcard})

@app.delete("/flashcards/{flashcard_id}")
def delete_flashcard(flashcard_id: int, response: Response, session: Session = Depends(get_session)):
    flashcard = session.get(Flashcard, flashcard_id)
    if flashcard:
        session.delete(flashcard)
        session.commit()
    
    response.headers["HX-Trigger"] = "flashcards-changed"
    return ""
@app.get("/flashcards/{flashcard_id}/edit", response_class=HTMLResponse)
def edit_flashcard_form(request: Request, flashcard_id: int, session: Session = Depends(get_session)):
    flashcard = session.get(Flashcard, flashcard_id)
    return templates.TemplateResponse(request=request, name="flashcard_edit.html", context={"card": flashcard})

@app.get("/flashcards/{flashcard_id}", response_class=HTMLResponse)
def read_flashcard(request: Request, flashcard_id: int, session: Session = Depends(get_session)):
    flashcard = session.get(Flashcard, flashcard_id)
    return templates.TemplateResponse(request=request, name="flashcard.html", context={"card": flashcard})

@app.put("/flashcards/{flashcard_id}", response_class=HTMLResponse)
def update_flashcard(
    request: Request,
    flashcard_id: int, 
    front: str = Form(...), 
    back: str = Form(...), 
    session: Session = Depends(get_session)
):
    flashcard = session.get(Flashcard, flashcard_id)
    flashcard.front = front
    flashcard.back = back
    session.add(flashcard)
    session.commit()
    session.refresh(flashcard)
    return templates.TemplateResponse(request=request, name="flashcard.html", context={"card": flashcard})

@app.delete("/flashcards/{flashcard_id}", response_class=HTMLResponse)
def delete_flashcard(flashcard_id: int, session: Session = Depends(get_session)):
    flashcard = session.get(Flashcard, flashcard_id)
    session.delete(flashcard)
    session.commit()
    return ''

@app.get("/study/{deck_id}", response_class=HTMLResponse)
def study_deck(request: Request, deck_id: int, session: Session = Depends(get_session)):
    deck = session.get(Deck, deck_id)
    if not deck:
        return "Deck não encontrado"

    statement = select(Flashcard).where(
        Flashcard.deck_id == deck_id,
        Flashcard.next_review <= date.today()
    ).order_by(Flashcard.last_reviewed.asc())
    
    due_flashcards = session.exec(statement).all()

    card_to_review = due_flashcards[0] if due_flashcards else None
    
    return templates.TemplateResponse(
        request=request, 
        name="study.html", 
        context={"deck": deck, "card": card_to_review}
    )
    
@app.get("/study/card/{card_id}/back", response_class=HTMLResponse)
def study_card_back(request: Request, card_id: int, session: Session = Depends(get_session)):
    card = session.get(Flashcard, card_id)
    return templates.TemplateResponse(request=request, name="study_back.html", context={"card": card})

@app.put("/flashcards/{flashcard_id}/review", response_class=HTMLResponse)
def review_flashcard(
    request: Request, 
    flashcard_id: int, 
    correct: bool, 
    session: Session = Depends(get_session)
):
    current_card = session.get(Flashcard, flashcard_id)
    deck_id = current_card.deck_id
    
    # Repetição Espaçada
    if correct:
        current_card.next_review = date.today() + timedelta(days=current_card.interval)
        current_card.interval = current_card.interval * 2
    else:
        current_card.interval = 1
        
    current_card.last_reviewed = datetime.now()
        
    session.add(current_card)
    session.commit()
    
    statement = select(Flashcard).where(
        Flashcard.deck_id == deck_id,
        Flashcard.next_review <= date.today()
    ).order_by(Flashcard.last_reviewed.asc())
    
    due_cards = session.exec(statement).all()
    
    if not due_cards:
        html = """
        <div class='card' id='study-card-container'>
            <h2>Fim!</h2>
            <p>Não há mais flashcards a revisar neste deck hoje.</p>
            <a href='/'><button>Home</button></a>
        </div>
        """
        return HTMLResponse(content=html)
        
    return templates.TemplateResponse(request=request, name="study_front.html", context={"card": due_cards[0]})

@app.get("/decks_list", response_class=HTMLResponse)
def get_decks_list(request: Request, q: str = "", page: int = 1, session: Session = Depends(get_session)):
    limit = 5
    offset = (page - 1) * limit
    
    statement = select(Deck)
    
    if q:
        statement = statement.where(Deck.name.contains(q))
        
    statement = statement.order_by(Deck.id.desc())
    
    total_decks = len(session.exec(statement).all())
    decks = session.exec(statement.offset(offset).limit(limit)).all()
    has_next = total_decks > offset + limit
    total_pages = max(1, (total_decks + limit - 1) // limit)
    
    return templates.TemplateResponse(
        request=request, 
        name="deck_list.html", 
        context={"decks": decks, "page": page, "q": q, "has_next": has_next, "total_pages": total_pages}
    )

@app.get("/decks/{deck_id}/flashcards", response_class=HTMLResponse)
def get_flashcards_list(request: Request, deck_id: int, q: str = "", page: int = 1, session: Session = Depends(get_session)):
    limit = 5
    offset = (page - 1) * limit
    
    statement = select(Flashcard).where(Flashcard.deck_id == deck_id)
    
    if q:
        statement = statement.where((Flashcard.front.contains(q)) | (Flashcard.back.contains(q)))
        
    statement = statement.order_by(Flashcard.id.desc())
    
    total_cards = len(session.exec(statement).all())
    flashcards = session.exec(statement.offset(offset).limit(limit)).all()
    has_next = total_cards > offset + limit
    total_pages = max(1, (total_cards + limit - 1) // limit)
    
    return templates.TemplateResponse(
        request=request, 
        name="flashcard_list.html", 
        context={
            "flashcards": flashcards, 
            "deck_id": deck_id, 
            "page": page, 
            "q": q, 
            "has_next": has_next,
            "total_pages": total_pages
        }
    )
    
@app.delete("/decks/{deck_id}")
def delete_deck(deck_id: int, response: Response, session: Session = Depends(get_session)):
    deck = session.get(Deck, deck_id)
    if deck:
        session.delete(deck)
        session.commit()
        
    response.headers["HX-Redirect"] = "/"
    return 