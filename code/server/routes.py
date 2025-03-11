from pathlib import Path
from uuid import UUID, uuid4
from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse
from datatypes import Content, Product
from pydantic import BaseModel

import services

router = APIRouter()
TEMP_DIR = "./temp_images"
SERVER_URL = "http://localhost:8000"


class CaptionedImage(BaseModel):
    temp_image_id: UUID
    caption: str


def save_temp_image(image) -> tuple[str, UUID]:
    temp_image_id = uuid4()
    image_path_dir = Path(TEMP_DIR) / str(temp_image_id)
    image_path_dir.mkdir()
    image_path = image_path_dir / image.filename

    with open(image_path, "wb") as dst:
        dst.write(image.file.read())
    return image_path, temp_image_id


def get_temp_image(temp_image_id: UUID):
    image_dir = Path(TEMP_DIR) / str(temp_image_id)
    image_dir = image_dir.absolute()
    image_path = next(image_dir.iterdir())
    return image_path


@router.post("/image")
async def image_caption(image: UploadFile) -> CaptionedImage:
    image_path, temp_image_id = save_temp_image(image)

    caption = services.image_captioning(image_path)

    return CaptionedImage(temp_image_id=temp_image_id, caption=caption)


@router.post("/generate")
async def content_generation(caption: str) -> Content:
    content: Content = services.content_generation(one_line_description=caption)
    return content


@router.post("/products")
async def post_products(content: Content, temp_image_id: UUID) -> dict[str, str]:
    image_path = get_temp_image(temp_image_id)
    id: UUID = services.save_product(content, image_path)
    return {"product_id": str(id)}


class ProductResponse(BaseModel):
    id: UUID
    content: Content
    image_id: UUID
    image_uri: str


class ProductsWithAnswer(BaseModel):
    answer: str
    products: list[ProductResponse]


@router.get("/search")
async def search(query: str) -> ProductsWithAnswer:
    answer, products = services.text_search_with_answer(query)
    product_responses = [
        ProductResponse(
            id=product.id,
            content=product.content,
            image_id=product.image_id,
            image_uri=f"{SERVER_URL}/api/v1/image?id={product.image_id}",
        )
        for product in products
    ]
    return ProductsWithAnswer(answer=answer, products=product_responses)


@router.get("/similar_products")
async def similar_products(product_id: UUID) -> list[ProductResponse]:
    products = services.find_similar(product_id)
    product_responses = [
        ProductResponse(
            id=product.id,
            content=product.content,
            image_id=product.image_id,
            image_uri=f"{SERVER_URL}/api/v1/image?id={product.image_id}",
        )
        for product in products
    ]
    return product_responses


@router.post("/image_search")
async def image_search(image: UploadFile) -> list[ProductResponse]:
    image_uri, _ = save_temp_image(image)
    products = services.image_search(image_uri=image_uri)
    product_responses = [
        ProductResponse(
            id=product.id,
            content=product.content,
            image_id=product.image_id,
            image_uri=f"{SERVER_URL}/api/v1/image?id={product.image_id}",
        )
        for product in products
    ]
    return product_responses


@router.get("/homepage")
async def homepage() -> list[ProductResponse]:
    products = services.home_screen()
    product_responses = [
        ProductResponse(
            id=product.id,
            content=product.content,
            image_id=product.image_id,
            image_uri=f"{SERVER_URL}/api/v1/image?id={product.image_id}",
        )
        for product in products
    ]
    return product_responses


@router.get("/image")
async def image(id: UUID) -> FileResponse:
    image_uri = services.get_image_uri(id)
    return FileResponse(path=image_uri)


@router.get("/product")
async def product(product_id: UUID) -> ProductResponse:
    pass
