from sqlmodel import Session, create_engine

from app.core.settings import settings

if settings.database_type == "sqlite":
    engine = create_engine(
        settings.database_url, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(settings.database_url)


def get_session():
    with Session(engine) as session:
        yield session


def save(model_instance, *, db: Session):
    """Saves an instance of any object to the database."""
    db.add(model_instance)
    db.commit()
    db.refresh(model_instance)

    return model_instance


def delete(model_instance, *, db: Session):
    """Delete an instance of an object from the database."""
    db.delete(model_instance)
    db.commit()
