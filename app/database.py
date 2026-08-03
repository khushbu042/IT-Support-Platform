from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


class Base(DeclarativeBase):
    pass


with engine.connect() as connection:
    result = connection.execute(text("SELECT 1"))
    print(result.scalar())
