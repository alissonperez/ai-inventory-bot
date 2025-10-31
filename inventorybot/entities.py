import os
import random
import string
from dataclasses import dataclass
from typing import Optional
from enum import Enum

from slugify import slugify


# Enum
class Status(Enum):
    DISPONIVEL = "disponivel"
    INDISPONIVEL = "indisponivel"
    EMPRESTADO = "emprestado"
    QUEBRADO = "quebrado"


@dataclass
class Location:
    name: str
    location: Optional["Location"] = None

    def filename(self):
        return f"{slugify(self.name)} - Inventário"

    def __str__(self):
        return self.name

    def to_dict(self):
        return {
            "name": self.name,
            "filename": self.filename(),
            "location": self.location.to_dict() if self.location else "",
        }


@dataclass
class Item:
    NUM_RANDOM_CHARS_FILENAME = 6

    name: Optional[str] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
    size: Optional[str] = None
    status: Status = Status.DISPONIVEL
    photo: Optional[str] = None
    tags: Optional[list[str]] = None

    borrowed_by: Optional[str] = None
    borrowed_date: Optional[str] = None

    location: Optional[Location] = None

    def validate(self):
        if self.name is None:
            raise ValueError("Nome é obrigatório")

        if self.quantity is None:
            raise ValueError("Quantidade é obrigatória")

        if self.location is None:
            raise ValueError("Localização é obrigatória")

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description or "",
            "quantity": self.quantity,
            "size": self.size or "",
            "status": self.status.value,
            "photo": self.photo or "",
            "tags": self.tags or [],
            "borrowed_by": self.borrowed_by,
            "borrowed_date": self.borrowed_date,
            "location": self.location.to_dict() if self.location else None,
        }

    def cover_filename(self):
        if not self.photo:
            return None

        # filename from path
        filename = os.path.basename(self.photo)
        return filename

    def filename(self):
        random_id = "".join(
            random.choice(string.ascii_lowercase + string.digits)
            for _ in range(self.NUM_RANDOM_CHARS_FILENAME)
        )

        return f"{slugify(self.name)}-{random_id}"

    def __str__(self):
        return f"{self.name} ({self.quantity})"

    def __repr__(self):
        return f"Item(name={self.name}, quantity={self.quantity}, size={self.size}, status={self.status}, photo={self.photo}, borrowed_by={self.borrowed_by}, borrowed_date={self.borrowed_date}, location={self.location})"
