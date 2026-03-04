from sqlmodel import create_engine, SQLModel

DATABASE_URL = "sqlite:///./chatbot.db"
engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    SQLModel.metadata.create_all(engine)
