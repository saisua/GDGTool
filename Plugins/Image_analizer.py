#from transformers import ViTFeatureExtractor, ViTForImageClassification
#from transformers import SegformerFeatureExtractor, SegformerForImageClassification
from transformers import AutoFeatureExtractor, AutoModelForImageClassification
from transformers import pipeline
from PIL import Image
import requests
import numpy as np
import tensorflow as tf

#from Core.Crawler import Crawler

model_name = "google/vit-base-patch16-224"
feature_extractor = AutoFeatureExtractor.from_pretrained(model_name)
model = AutoModelForImageClassification.from_pretrained(model_name)
model.eval()
feat = feature_extractor(images=Image.open(requests.get("https://res.cloudinary.com/roundglass/image/upload/v1589190869/roundglass/sustain/Indian-pangolin_Ansar-Khan-copy_brwnan.png", stream=True).raw)
                                                    )#, return_tensors="tf", padding=True)
res = model(tf.constant(feat["pixel_values"]))
#print(model.config.id2label[model(
#                                feature_extractor(
#                                                    images=Image.open(requests.get("https://res.cloudinary.com/roundglass/image/upload/v1589190869/roundglass/sustain/Indian-pangolin_Ansar-Khan-copy_brwnan.png", stream=True).raw)
#                                                    , return_tensors="pt", padding=True)["pixel_values"]
#                                ).logits.argmax(-1).item()])
pp = pipeline(task="image-classification", device=-1)
pp(images="https://res.cloudinary.com/roundglass/image/upload/v1589190869/roundglass/sustain/Indian-pangolin_Ansar-Khan-copy_brwnan.png")

def mp_image_recognition(data):
    recognized:list = []
    for url in data["images"]:
        recognized.append(model.config.id2label[model(**feature_extractor(
                                                    images=Image.open(requests.get(url, stream=True).raw)
                                                    , return_tensors="tf")
                                ).logits.argmax(-1).item()])
        print("image done!")

    data["recognized"] = recognized
    # I think here I don't need 
    data["locks"] -= 1

async def image_recognition(crawler:Crawler, data:dict, page:object):
    if("images" in data):
        with data._mutex:
            data["locks"] = data.get("locks", 0) + 1

        print(f"Analizing {len(data['images'])} images")
        mp_image_recognition(data)
        #crawler.pool.apply_async(mp_image_recognition, (data,))

def setup(crawler:Crawler):
    if(crawler.get_images not in crawler._page_management):
        crawler.add_pipe("page", crawler.get_images, "Image extractor")
    if(image_recognition not in crawler._data_management):
        crawler.add_pipe("data", image_recognition, "Image recognition")
