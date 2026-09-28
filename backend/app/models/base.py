import uuid
from typing import Any
from datetime import datetime, timezone
from sqlalchemy.orm import as_declarative, declared_attr, Mapped, mapped_column
from sqlalchemy import DateTime

@as_declarative()
class Base:
    id: Any
    __name__: str

    @declared_attr
    def __tablename__(cls) -> str:
        # Convert CamelCase to snake_case for tablenames
        import re
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', cls.__name__)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

def uuid_gen():
    return uuid.uuid4()

def utc_now():
    return datetime.now(timezone.utc)
