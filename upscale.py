from cachetools import cached

import cv2
import numpy as np
from cv2 import dnn_superres

@cached({})
def get_scaler(model_path: str) -> dnn_superres.DnnSuperResImpl:
    scaler = dnn_superres.DnnSuperResImpl.create()
    scaler.readModel(model_path)
    scaler.setModel("edsr", 2)

    return scaler

def upscale(input_file: bytes, format: str, model_path: str = "EDSR_x2.pb") -> bytes:
    """
    :param input_path: путь к изображению для апскейла
    :param output_path:  путь к выходному файлу
    :param model_path: путь к ИИ модели
    :return:
    """

    scaler = get_scaler(model_path)
    nparr = np.frombuffer(input_file, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    _, result = cv2.imencode(format, scaler.upsample(image))
    
    return result.tobytes()

if __name__ == "__main__":
    with open("file.png", "rb") as file:
        result = upscale(file.read())

    with open("new_file.png", "wb") as file:
        file.write(result)
