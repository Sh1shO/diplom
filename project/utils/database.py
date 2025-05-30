from contextlib import contextmanager
from db import Session

@contextmanager
def get_session():
    """Контекстный менеджер для получения сессии базы данных."""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()