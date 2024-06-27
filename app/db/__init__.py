# from sqlmodel import Session, SQLModel, create_engine

# from app.core.settings import settings
# from app import models

# sqlite_url = settings.database_url

# connect_args = {"check_same_thread": False}
# engine = create_engine(sqlite_url, echo=False, connect_args=connect_args)
# SQLModel.metadata.create_all(engine)


# def get_session():
#     with Session(engine) as session:
#         yield session
