from typing import List, Optional
from datetime import date, datetime, timedelta
from sqlmodel import Field, Relationship, SQLModel, create_engine

class Deck(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    
    flashcards: List["Flashcard"] = Relationship(back_populates="deck")

class Flashcard(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    front: str
    back: str
    interval: int = Field(default=1)
    next_review: date = Field(default_factory=date.today)
    last_reviewed: datetime = Field(default_factory=datetime.now)
    
    # Relacionamento 1:N
    deck_id: Optional[int] = Field(default=None, foreign_key="deck.id")
    deck: Optional[Deck] = Relationship(back_populates="flashcards")
    
    @property
    def formatted_next_review(self) -> str:
        today = date.today()
        if self.next_review <= today:
            return "hoje"
        elif self.next_review == today + timedelta(days=1):
            return "amanhã"
        else:
            return self.next_review.strftime("%d/%m/%Y")

# Configuração do Banco
sqlite_file_name = "flashcards.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)