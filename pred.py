import cv2
import numpy as np

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2' 

import tensorflow as tf
from tensorflow.keras.models import load_model
import pickle

MODEL_FILENAME = "7layers_mix.h5"
MODEL_LABELS_FILENAME = "labels.dat"

# Load up the model labels (so we can translate model predictions to actual letters)
with open(MODEL_LABELS_FILENAME, "rb") as f:
    lb = pickle.load(f)

# Load the trained neural network
model = load_model(MODEL_FILENAME)


def pred_captcha(img, words):
    lines_pos = [i * 30 for i in range(0, words + 1)]
    parts = []
    for i, ln in enumerate(lines_pos[:-1]):
        parts.append(img[:, ln: lines_pos[i + 1] - 1])
    parts = np.stack(parts, axis=0)

    # print(text)
    # cv2.imwrite("cap.jpg", captcha_image)
    # for part in parts:
    #     cv2.imshow('captcha', part)
    #     cv2.waitKey(0)

    prediction = model.predict(parts, verbose=0)
    return ''.join(lb.inverse_transform(prediction))
