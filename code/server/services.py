import json
import random
import torch
from PIL import Image
from transformers import VisionEncoderDecoderModel, ViTImageProcessor, GPT2TokenizerFast
from tqdm import tqdm
from uuid import UUID, uuid4

from db import FileStore, SqlLiteDB
from datatypes import Content, Product

# device = "cuda" if torch.cuda.is_available() else "cpu"
device = "cuda" if torch.cuda.is_available() else "cpu"
captioning_model = VisionEncoderDecoderModel.from_pretrained(
    "nlpconnect/vit-gpt2-image-captioning"
).to(device)
captioning_image_processor = ViTImageProcessor.from_pretrained(
    "nlpconnect/vit-gpt2-image-captioning"
)
captioning_tokenizer = GPT2TokenizerFast.from_pretrained(
    "nlpconnect/vit-gpt2-image-captioning"
)


# Note image can be either an file pointer or an path
def image_captioning(image) -> str:

    image = Image.open(image)

    # Preprocessing the Image
    img = captioning_image_processor(image, return_tensors="pt").to(device)

    # Generating captions
    output = captioning_model.generate(**img)

    # decode the output
    caption = captioning_tokenizer.batch_decode(output, skip_special_tokens=True)[0]

    return caption


from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOllama(model="llama3.2", num_predict=1024, format="json")


def content_generation(one_line_description: str) -> Content:
    system_prompt = """Given an one line description of a product generate mock data for an e-commerce site.
Make up dimensions and metrics if not given by the user.

The response must be of the following JSON format:
<format>
{{
  "title": "title for the product",
  "content": "product details like description, features and dimesions with neat heading, text highlighting in markdown format",
  "tags": [5 relevant tags for search]
}}
</format>
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                system_prompt,
            ),
            ("human", "{input}"),
        ]
    )

    chain = prompt | llm
    response = chain.invoke(
        {
            "input": one_line_description,
        }
    )

    # --FEATURE: Replace with Pydantic and streams
    content_dict = json.loads(response.content)

    content = Content(
        content=content_dict["content"],
        tags=content_dict["tags"],
        title=content_dict["title"],
    )
    return content


blobstore = FileStore()
db = SqlLiteDB()

from langchain_ollama import OllamaEmbeddings
from langchain_experimental.open_clip import OpenCLIPEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

text_embeddings = OllamaEmbeddings(model="nomic-embed-text")

# %pip install --upgrade --quiet  langchain-experimental
clip_embeddings = OpenCLIPEmbeddings(
    model_name="ViT-B-32", checkpoint="commonpool_m_laion_s128m_b4k"
)

content_index = Chroma(
    collection_name="content",
    embedding_function=text_embeddings,
    persist_directory="./chroma_db",
)

image_index = Chroma(
    collection_name="images",
    embedding_function=clip_embeddings,
    persist_directory="./chroma_db",
)


def save_product(content: Content, image_path: str) -> UUID:
    image_id: UUID = blobstore.save_image(image_path)
    id: UUID = uuid4()
    product = Product(
        id=id,
        content=content,
        image_id=image_id,
    )

    db.save_product(product)

    # Index image & content
    document = Document(
        page_content=content.content,
        id=str(id),
    )

    content_index.add_documents(documents=[document], ids=[str(id)])

    image_index.add_images(
        uris=[blobstore.get_image_uri(image_id)],
        ids=[str(id)],
        metadatas=[{"product_id": str(id)}],
    )

    return id


def tag_based_filtering(tag: list[str], limit: int = 10, skip: int = 0):
    products: list[Product] = db.filter_by_tag(tag, limit, skip)
    return products


def image_search(image_uri: str) -> list[Product]:
    results = image_index.similarity_search_by_image(uri=image_uri)
    print(results)
    product_ids = [UUID(result.metadata["product_id"]) for result in results]
    products = db.get_products(product_ids)
    return products


def text_search(query: str) -> list[Product]:
    results = content_index.similarity_search(query)
    product_ids = [UUID(result.id) for result in results]
    products = db.get_products(product_ids)
    return products


from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain


def text_search_with_answer(query: str) -> tuple[str, list[Product]]:
    # --FEATURE: Can use agent to decide if answer needs to be generated
    retriever = content_index.as_retriever()

    prompt = ChatPromptTemplate.from_template(
        """Answer the following question based only on the provided context:

    <context>
    {context}
    </context>

    Question: {input}"""
    )

    document_chain = create_stuff_documents_chain(llm, prompt)
    retrieval_chain = create_retrieval_chain(retriever, document_chain)
    response = retrieval_chain.invoke({"input": query})
    print(response)

    documents = response["context"]
    product_ids = [UUID(document.id) for document in documents]
    products = db.get_products(product_ids)

    answer = response["answer"]
    return answer, products


def find_similar(product_id: UUID) -> list[Product]:
    product: Product | None = db.get_product(product_id)

    if product == None:
        return []

    image_id: UUID = product.image_id
    image_uri = blobstore.get_image_uri(image_id)
    content: Content = product.content
    text_results: list[Product] = text_search(content.content)
    image_results: list[Product] = image_search(image_uri)

    # De-Duplicate
    results = set(text_results + image_results)
    results: list[Product] = list(results)
    return results


def shopping_planner_agent():
    pass


def home_screen() -> list[Product]:
    ids = db.get_ids()
    product_ids = [UUID(id) for id in random.choices(ids, k=6)]
    return db.get_products(product_ids)


def get_image_uri(image_id: UUID) -> str:
    return blobstore.get_image_uri(str(image_id))
