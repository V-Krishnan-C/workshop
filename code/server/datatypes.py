from dataclasses import dataclass
from uuid import UUID


@dataclass
class Content:
    title: str
    content: str
    tags: list[str]


@dataclass
class Product:
    id: UUID
    content: Content
    image_id: UUID

    def __hash__(self):
        return hash(self.id)
