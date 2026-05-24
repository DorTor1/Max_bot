from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from pass_bot.infrastructure.config.settings import Settings

_engine = None
_SessionLocal: sessionmaker[Session] | None = None


def init_db(settings: Settings) -> None:
    global _engine, _SessionLocal
    _engine = create_engine(settings.database_url, pool_pre_ping=True)
    _SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


def get_engine():
    if _engine is None:
        raise RuntimeError("DB not initialized; call init_db() first")
    return _engine


@contextmanager
def session_scope() -> Generator[Session]:
    if _SessionLocal is None:
        raise RuntimeError("DB not initialized")
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
