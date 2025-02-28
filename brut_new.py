"""
This script performs Aadhar masking using OpenCV and pytesseract-OCR.
"""

import datetime
import sys
import os
import math
import shutil
import uuid
import multiprocessing
import tkinter as tk
from tkinter import filedialog, messagebox
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import cv2
from scipy import ndimage
import numpy as np
from PIL import Image
from pdf2image import convert_from_path
from yolo_model import process_image
from temp_aadhar import AadhaarCard
from registry import update_processed_count, get_processed_count

documents_path = os.path.join(os.environ["USERPROFILE"], "Documents")
UNPROCESSED_FOLDER = os.path.join(documents_path, "unprocessed_files")

os.makedirs(UNPROCESSED_FOLDER, exist_ok=True)

MAX_AADHAARS = 600


config = {
    'orient': True,
    'skew': False,
    'crop': True,
    'contrast': True,
    'psm': [3, 4, 6],
    'mask_color': (0, 0, 0),  # Mask color in BGR
    'brut_psm': [6]
}

# Initialize the AadhaarCard processor
aadhaar_processor = AadhaarCard(config)


def rotate_only(path, degrees):
    """rotates the images with 90 degrees on to the anticlockwise location"""
    img = cv2.imread(str(path))
    angle_in_degrees = degrees
    rotated = ndimage.rotate(img, angle_in_degrees)
    cv2.imwrite(path, rotated)
    return rotated


def rotate_img(img, degrees):
    """rotates the images for the calculated median angle"""
    angle_in_degrees = degrees
    rotated = ndimage.rotate(img, angle_in_degrees)
    return rotated


def rotate(path):
    """rotates the images based on the median angle calculated"""
    # GrayScale Conversion for the Canny Algorithm
    img = cv2.imread(str(path))
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # self.display(img_gray)
    # Canny Algorithm for edge detection was developed by John F. Canny not
    # Kennedy!! :)
    img_edges = cv2.Canny(img_gray, 100, 100, apertureSize=3)
    # self.display(img_edges)
    # Using Houghlines to detect lines
    lines = cv2.HoughLinesP(
        img_edges,
        1,
        math.pi / 180.0,
        100,
        minLineLength=100,
        maxLineGap=5)
    img_copy = img.copy()
    for x in range(0, len(lines)):
        for x1, y1, x2, y2 in lines[x]:
            cv2.line(img_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)

    angles = []
    for x1, y1, x2, y2 in lines[0]:
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        angles.append(angle)

    # Getting the median angle
    median_angle = np.median(angles)
    if (median_angle >= 45 or median_angle <= -45):
        return img
    print(f"Correcting angle by {median_angle} degrees")
    return rotate_img(img, median_angle)


def multi_page_pdf(arg, masked_filename):
    """handles the pdfs with multiple images"""
    os.makedirs('temp_images', exist_ok=True)
    list1 = []
    list2 = []
    for i, img in enumerate(arg):
        temp_file_path = f"temp_images/page_{uuid.uuid4().hex}_{i + 1}.png"
        img.save(temp_file_path, "PNG")
        masked_name_path = f"temp_images/masked_page_{
            uuid.uuid4().hex}_{
            i + 1}.jpg"
        list1.append((temp_file_path, masked_name_path))

    # def process_page(page_args):
    #     temp_path, masked_path = page_args
    #     print(temp_path)
    #     print(masked_path)
    #     result = process_aadhaar(temp_path, masked_path)
    #     list2.append(result)

    # threads = []
    # for page_args in list1:
    #     thread = Thread(target=process_page, args=(page_args,))
    #     threads.append(thread)
    #     thread.start()

    # for thread in threads:
    #     thread.join()

    for i in range(len(arg)):
        result = process_aadhaar(*list1[i])
        list2.append(result)

    first_image = Image.open(list2[0])
    image_objects = [Image.open(img) for img in list2[1:]]
    first_image.save(
        masked_filename,
        format="PDF",
        save_all=True,
        append_images=image_objects)


def process_aadhaar(filepath, savename):
    """Processes the image for Aadhar masking."""
    try:
        temp_file = f"temp_{uuid.uuid4().hex}.jpg"
        output_path = None
        aadhaar_detected = False

        if os.path.isfile(filepath) and filepath.lower().endswith('.pdf'):
            pdf_to_image = convert_from_path(filepath, dpi=120)
            if len(pdf_to_image) > 1:
                multi_page_pdf(pdf_to_image, savename)
                return True
            output_path = os.path.splitext(filepath)[0] + ".png"
            pdf_to_image[0].save(output_path, "PNG")
            filepath = output_path

        for i in range(4):
            cv_img = rotate(filepath if i == 0 else temp_file)
            cv2.imwrite(temp_file, cv_img)

            # Process with both contrast methods
            for contrast_mode in [0, 1]:
                extracted_aadhaars = aadhaar_processor.extract(
                    temp_file, contrast_mode)
                if extracted_aadhaars:
                    aadhaar_detected = True  # Aadhaar found
                    aadhaar_processor.mask_image(
                        temp_file, temp_file, extracted_aadhaars)
                

            rotate_only(temp_file, 90)

        processFlag=process_image(temp_file)
        

        if not processFlag:
            aadhaar_detected=True

        if not aadhaar_detected:
            # Copy file to unprocessed folder if Aadhaar is not found
            shutil.copy2(filepath, os.path.join(UNPROCESSED_FOLDER, os.path.basename(filepath)))
            print(f"No Aadhaar detected. Copied {filepath} to {UNPROCESSED_FOLDER}.")
        else:
            aadhaar_processor.mask_image(temp_file, savename, extracted_aadhaars)

        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
        if output_path and os.path.exists(output_path):
            os.remove(output_path)
        return savename

    except Exception as e:
        print(f"Error processing {filepath}: {str(e)}")
        return None


def process_images_in_parallel(input_folder, output_folder):
    """Processes the images in parallel for lesser processing time."""
    processed_count = get_processed_count()
    

    if processed_count >= MAX_AADHAARS:
        messagebox.showerror("Limit Reached", "Processing limit of Aadhar cards reached.")
        return
    if not os.path.exists(input_folder):
        raise Exception("Input folder does not exist")

    tasks = []
    count = 0
    

    for filename in os.listdir(input_folder):
        if count + processed_count >= MAX_AADHAARS:
            break
        if filename.lower().endswith(
                ('.png', '.jpg', '.jpeg', '.pdf', '.bmp', '.gif', '.tiff')):
            input_path = os.path.join(input_folder, filename)
            name, ext = os.path.splitext(filename)
            output_path = os.path.join(output_folder, f"{name}_masked{ext}")
            tasks.append((input_path, output_path))
            count += 1

    with ProcessPoolExecutor(max_workers=cpu_count()) as executor:
        futures = []
        for input_path, output_path in tasks:
            future = executor.submit(process_aadhaar, input_path, output_path)
            futures.append(future)

        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    print(f"Successfully processed: {result}")
            except Exception as e:
                print(f"Task failed: {str(e)}")

    update_processed_count(processed_count + count)


def browse_input_folder():
    """browse the source images folder"""
    folder_path = filedialog.askdirectory(title="Select Input Folder")
    if folder_path:
        input_folder_var.set(folder_path)


def browse_output_folder():
    """browse the output images folder"""
    folder_path = filedialog.askdirectory(title="Select Output Folder")
    if folder_path:
        output_folder_var.set(folder_path)


def validate_and_process():
    """Validates the both folders and starts the process"""
    input_folder = input_folder_var.get()
    output_folder = output_folder_var.get()

    if not input_folder or not output_folder:
        messagebox.showerror(
            "Error", "Both input and output folders must be selected")
        return

    try:
        process_images_in_parallel(input_folder, output_folder)

    except Exception as e:
        messagebox.showerror("Error", f"Processing failed: {str(e)}")
    finally:
        if os.path.exists('temp_images'):
            shutil.rmtree('temp_images')
        root.destroy()


# GUI Setup
if __name__ == "__main__":
    # Check expiry
    multiprocessing.freeze_support()

    if datetime.datetime.now() > datetime.datetime(2025, 3, 4):
        messagebox.showerror(
            "Error", "This application has expired. Please contact support.")
        sys.exit()

    root = tk.Tk()
    root.title("Aadhaar Batch Processor")
    root.geometry("500x300")

    input_folder_var = tk.StringVar()
    output_folder_var = tk.StringVar()

    # GUI Layout
    tk.Label(
        root,
        text="Input Folder:",
        font=(
            "Arial",
            12)).pack(
        anchor="w",
        padx=10,
        pady=5)
    input_frame = tk.Frame(root)
    input_frame.pack(fill="x", padx=10)
    tk.Entry(
        input_frame,
        textvariable=input_folder_var,
        width=40).pack(
        side="left",
        fill="x",
        expand=True)
    tk.Button(
        input_frame,
        text="Browse",
        command=lambda: input_folder_var.set(
            filedialog.askdirectory())).pack(
        side="right",
        padx=5)

    tk.Label(
        root,
        text="Output Folder:",
        font=(
            "Arial",
            12)).pack(
        anchor="w",
        padx=10,
        pady=5)
    output_frame = tk.Frame(root)
    output_frame.pack(fill="x", padx=10)
    tk.Entry(
        output_frame,
        textvariable=output_folder_var,
        width=40).pack(
        side="left",
        fill="x",
        expand=True)
    tk.Button(
        output_frame,
        text="Browse",
        command=lambda: output_folder_var.set(
            filedialog.askdirectory())).pack(
        side="right",
        padx=5)

    tk.Button(root, text="Validate & Process",
              command=validate_and_process,
              font=("Arial", 12),
              bg="green", fg="white").pack(pady=20)
    root.mainloop()
