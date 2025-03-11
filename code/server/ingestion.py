from pathlib import Path
from PIL import Image
from tqdm import tqdm
from datatypes import Content
from services import image_captioning, content_generation, save_product

image_dir = "ingestion_images"
captions = []

for image_path in tqdm(Path(image_dir).iterdir()):
    try:
        caption = image_captioning(image_path)
        captions.append(caption)
        content: Content = content_generation(caption)
        save_product(content, str(image_path))
    except Exception as e:
        print(f"erro: {e}: in image {image_path.name}")

print(captions)
