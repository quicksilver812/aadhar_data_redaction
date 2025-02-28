import os
from ultralytics import YOLO
from huggingface_hub import hf_hub_download
from supervision import Detections
import cv2
import numpy as np
from PIL import Image

# Repo configuration
REPO_CONFIG = dict(
    repo_id="arnabdhar/YOLOv8-nano-aadhar-card",
    filename="model.pt",
    local_dir="./models"
)

# Load YOLO model
MODEL = YOLO(hf_hub_download(**REPO_CONFIG))
ID2LABEL = MODEL.names


def mask_aadhar_number(image_path, detections):
    """
    Masks detected AADHAR numbers in the image by filling them with black rectangles.

    Args:
        image_path (str): Path to the input image file.
        detections (Detections): Detection results from the YOLO model.

    Returns:
        PIL.Image: Image with AADHAR numbers masked.
    """
    # Load the image
    img = Image.open(image_path)
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

    # Mask each detected AADHAR_NUMBER
    for box, class_id in zip(detections.xyxy, detections.class_id):
        if ID2LABEL[class_id] == 'AADHAR_NUMBER':  # Filter for AADHAR_NUMBER
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(img_cv, (x1, y1), (x2, y2), (0, 0, 0), thickness=-1)  # Black out

    # Convert back to PIL Image for saving
    masked_img = Image.fromarray(cv2.cvtColor(img_cv, cv2.COLOR_BGR2RGB))
    return masked_img


def process_image(file_path):
    """
    Processes the input image to mask AADHAR numbers.

    Args:
        file_path (str): Path to the input image file.
        output_path (str): Path to save the masked image.
    """
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"The specified file does not exist: {file_path}")

    # Perform Inference
    detections = Detections.from_ultralytics(MODEL.predict(file_path)[0])


    detected_classes = detections.data.get('class_name', [])
     # Mask AADHAR numbers and save the image
    masked_img = mask_aadhar_number(file_path, detections)
    masked_img.save(file_path)
    
    # Check if "AADHAR_NUMBER" is in detected classes
    return "AADHAR_NUMBER" not in detected_classes
