from sqlalchemy import String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Item(Base):
    __tablename__ = "items"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)


def create_engine_and_session(url: str):
    engine = create_engine(url)
    return engine, sessionmaker(bind=engine, expire_on_commit=False)


def create_item(session_factory, name: str) -> int:
    """Example service transaction; database persistence is atomic."""
    if not name.strip():
        raise ValueError("name cannot be blank")
    with session_factory.begin() as session:
        item = Item(name=name)
        session.add(item)
        session.flush()
        item_id = item.id
    return item_id


if __name__ == "__main__":
    engine, factory = create_engine_and_session("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)  # Demo only; production uses Alembic.
    created_id = create_item(factory, "Example")
    with factory() as session:
        print(session.scalar(select(Item.name).where(Item.id == created_id)))
