from pathlib import Path
from typing import Protocol
from datatypes import Content, Product
from uuid import UUID, uuid4
import shutil


class BlobStore(Protocol):
    def save_image(image) -> int: ...
    def get_image_uri(image_id: str) -> str: ...


class Database(Protocol):
    def save_product(product: Product) -> int: ...
    def filter_by_tags(tags: list[str], limit: int, skip: int): ...
    def get_product(product_id: int): ...


class FileStore:
    def __init__(self, store="images"):
        self.store = store

    def save_image(self, image_path: str) -> UUID:
        id = uuid4()
        dst_dir = Path(self.store) / str(id)
        dst_dir.mkdir()
        file_name = Path(image_path).name
        dst_path = dst_dir / file_name
        shutil.copy(image_path, dst_path)
        return id

    def get_image_uri(self, image_id: UUID) -> str:
        image_uri_dir: Path = Path(self.store) / str(image_id)
        image_uri_dir = image_uri_dir.absolute()
        image_uri: Path = next(image_uri_dir.iterdir())
        return str(image_uri.absolute())


from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

engine = create_engine("sqlite:///database.db", echo=True)


class Base(DeclarativeBase):
    pass


class ProductModel(Base):
    __tablename__ = "product"
    id: Mapped[str] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(30))
    content: Mapped[str] = mapped_column()
    tags: Mapped[str] = mapped_column()
    image_id: Mapped[str] = mapped_column()


Base.metadata.create_all(engine)


class SqlLiteDB:
    def save_product(self, product: Product):
        with Session(engine) as session:
            product = ProductModel(
                id=str(product.id),
                title=product.content.title,
                content=product.content.content,
                tags=", ".join(product.content.tags),
                image_id=str(product.image_id),
            )
            session.add_all([product])
            session.commit()

    def filter_by_tag(self, tag: list[str], limit: int, skip: int) -> list[Product]:
        with Session(engine) as session:
            product_models = (
                session.query(ProductModel)
                .filter(ProductModel.tags.like(f"%tag%"))
                .offset(skip)
                .limit(limit)
            )

        products = [
            Product(
                id=UUID(product_model.id),
                content=Content(
                    content=product_model.content,
                    title=product_model.title,
                    tags=product_model.tags.split(", "),
                ),
                image_id=UUID(product_model.image_id),
            )
            for product_model in product_models
        ]

        return products

    def get_products(seld, product_ids: list[UUID]) -> list[Product]:
        product_ids = [str(product_id) for product_id in product_ids]

        with Session(engine) as session:
            product_models = (
                session.query(ProductModel)
                .filter(ProductModel.id.in_(product_ids))
                .all()
            )

        products = [
            Product(
                id=UUID(product_model.id),
                content=Content(
                    content=product_model.content,
                    title=product_model.title,
                    tags=product_model.tags.split(", "),
                ),
                image_id=UUID(product_model.image_id),
            )
            for product_model in product_models
        ]

        return products

    def get_product(self, product_id: UUID) -> Product | None:
        with Session(engine) as session:
            stmt = select(ProductModel).where(ProductModel.id == str(product_id))
            product_model = session.scalar(stmt)

        if product_model == None:
            return None

        return Product(
            id=UUID(product_model.id),
            content=Content(
                content=product_model.content,
                title=product_model.title,
                tags=product_model.tags,
            ),
            image_id=UUID(product_model.image_id),
        )

    def get_ids(self) -> list[int]:
        with Session(engine) as session:
            ids = session.query(ProductModel.id).limit(100)

        return [id[0] for id in ids]
