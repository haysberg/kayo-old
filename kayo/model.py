"""_summary_."""
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import MappedAsDataclass


class Base(MappedAsDataclass, DeclarativeBase):
    """Base SQLalchemy Class.

    Args:
        sqlalchemy.orm.DeclarativeBase (sqlalchemy.orm.DeclarativeBase): Don't question it.
    """

    pass
