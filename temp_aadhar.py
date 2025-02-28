"""This module contains functions to extract Uid's and mask the aadhar images"""

import re
import os
from dotenv import load_dotenv
import cv2
import pytesseract
from pytesseract import Output
from PIL import Image

load_dotenv()

TESSERACT_PATH = os.getenv("TESSERACT_PATH")

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class AadhaarCard:
    """Class for Aadhaar card processing, including UID extraction and image masking."""


    def __init__(self, config):
        """Initialize Aadhaar_Card with a configuration dictionary.

        Args:
            config (dict): Configuration settings for processing.
        """
        self.config = config

    def validate(self, aadhar_num):
        """Validate if the given Aadhaar number is valid.

        Args:
            aadhar_num (str): Aadhaar number as a string.

        Returns:
            int: 1 if valid, 0 if invalid.
        """
        mult = [
            [
                0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [
                1, 2, 3, 4, 0, 6, 7, 8, 9, 5], [
                2, 3, 4, 0, 1, 7, 8, 9, 5, 6], [
                    3, 4, 0, 1, 2, 8, 9, 5, 6, 7], [
                        4, 0, 1, 2, 3, 9, 5, 6, 7, 8], [
                            5, 9, 8, 7, 6, 0, 4, 3, 2, 1], [
                                6, 5, 9, 8, 7, 1, 0, 4, 3, 2], [
                                    7, 6, 5, 9, 8, 2, 1, 0, 4, 3], [
                                        8, 7, 6, 5, 9, 3, 2, 1, 0, 4], [
                                            9, 8, 7, 6, 5, 4, 3, 2, 1, 0]]

        perm = [
            [
                0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [
                1, 5, 7, 6, 2, 8, 3, 0, 9, 4], [
                5, 8, 0, 3, 7, 9, 6, 1, 4, 2], [
                    8, 9, 1, 6, 0, 4, 3, 5, 2, 7], [
                        9, 4, 5, 3, 1, 2, 6, 8, 7, 0], [
                            4, 2, 8, 6, 5, 7, 3, 9, 0, 1], [
                                2, 7, 9, 3, 8, 0, 6, 4, 1, 5], [
                                    7, 0, 4, 6, 9, 1, 3, 2, 5, 8]]

        try:
            i = len(aadhar_num)
            j = 0
            x = 0

            while i > 0:
                i -= 1
                x = mult[x][perm[(j % 8)][int(aadhar_num[i])]]
                j += 1
            if x == 0:
                return 1            
            return 0

        except ValueError:
            return 0
        except IndexError:
            return 0

    def extract(self, path, setting):
        """Extract Aadhaar numbers from the given image.

        Args:
            path (str): Path to the Aadhaar image.
            setting (int): Contrast setting for processing.

        Returns:
            list: List of extracted Aadhaar numbers.
        """
        self.image_path = path
        self.read_image_cv()

        if self.config['skew']:
            print("Skewness correction not available")

        if self.config['crop']:
            print("Smart Crop not available")

        # self.save_image(self.cv_img)

        if self.config['contrast']:
            if setting == 0:
                self.cv_img = self.contrast_image_trunc(self.cv_img)
                print("Correcting trunc contrast")
            else:
                self.cv_img = self.contrast_image_binary(self.cv_img)
                print("Correcting thresh contrast")

        aadhaars = set()
        for i in range(len(self.config['psm'])):
            t = self.text_extractor(self.cv_img, self.config['psm'][i])
            anum = self.is_aadhaar_card(t)
            uid = self.find_uid(t)

            if anum != "Not Found" and len(uid) == 0:
                if len(anum) - anum.count(' ') == 12:
                    aadhaars.add(anum.replace(" ", ""))
            if anum == "Not Found" and len(uid) != 0:
                aadhaars.add(uid[0].replace(" ", ""))
            if anum != "Not Found" and len(uid) != 0:
                if len(anum) - anum.count(' ') == 12:
                    aadhaars.add(anum.replace(" ", ""))
                aadhaars.add(uid[0].replace(" ", ""))

        return list(aadhaars)

    def mask_image(self, path, write, aadhaar_list):
        """Mask Aadhaar numbers in the given image.

        Args:
            path (str): Path to the input image.
            write (str): Path to save the masked image.
            aadhaar_list (list): List of Aadhaar numbers to be masked.

        Returns:
            int: Number of masked occurrences.
        """
        self.mask_count = 0
        self.mask = cv2.imread(str(path), cv2.IMREAD_COLOR)
        for j in range(len(self.config['psm'])):
            for i in range(len(aadhaar_list)):
                if self.mask_aadhaar(
                        aadhaar_list[i],
                        write,
                        self.config['psm'][j]) > 0:
                    self.mask_count += 1

        if write.lower().endswith('.pdf'):
            img2pdf = Image.open(path)
            img2pdf.save(write, "PDF")
        else:
            cv2.imwrite(write, self.mask)
        return self.mask_count

    def mask_aadhaar(self, uid, out_path, psm):
        """Mask a specific Aadhaar number in an image.

        Args:
            uid (str): Aadhaar number to mask.
            out_path (str): Path to save the output image.
            psm (int): Tesseract PSM mode.

        Returns:
            int: Count of matches found and masked.
        """
        d = self.box_extractor(self.mask, psm)
        n_boxes = len(d['level'])
        color = self.config['mask_color']
        count_of_match = 0
        for i in range(n_boxes):
            string = d['text'][i].strip()
            if string.isdigit() and string in uid and len(string) >= 2:
                (x, y, w, h) = (d['left'][i], d['top']
                                [i], d['width'][i], d['height'][i])
                cv2.rectangle(
                    self.mask, (x, y), (x + w, y + h), color, cv2.FILLED)
                count_of_match += 1
        return count_of_match

    def read_image_cv(self):
        """Read an image using OpenCV and store it in an instance variable."""
        self.cv_img = cv2.imread(str(self.image_path), cv2.IMREAD_COLOR)

    def mask_nums(self, input_file, output_file):
        """Mask all numeric values in an image.

        Args:
            input_file (str): Path to the input image.
            output_file (str): Path to save the output image.

        Returns:
            str: Status message.
        """
        img = cv2.imread(str(input_file), cv2.IMREAD_COLOR)
        for i in range(len(self.config['brut_psm'])):  # 'brut_psm': [6]
            d = self.box_extractor(img, self.config['brut_psm'][i])
            n_boxes = len(d['level'])
            color = self.config['mask_color']  # BGR
            for i in range(n_boxes):
                string = d['text'][i].strip()
                if string.isdigit() and len(string) >= 1:
                    (x, y, w, h) = (d['left'][i], d['top']
                                    [i], d['width'][i], d['height'][i])
                    cv2.rectangle(
                        img, (x, y), (x + w, y + h), color, cv2.FILLED)

        cv2.imwrite(output_file, img)
        return "Done"

    # def save_image(self, img):
    #     cv2.imwrite('temp.jpg', img)

    def contrast_image_trunc(self, img):
        """Apply truncation-based contrast enhancement to an image.

        Args:
            img (numpy.ndarray): Input image.

        Returns:
            numpy.ndarray: Processed image.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_TRUNC | cv2.THRESH_OTSU)[1]
        return thresh

    def contrast_image_binary(self, img):
        """Apply binary threshold-based contrast enhancement.

        Args:
            img (numpy.ndarray): Input image.

        Returns:
            numpy.ndarray: Processed image.
        """
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        return thresh

    def text_extractor(self, img, psm):
        """Extract text from an image using OCR.

        Args:
            img (numpy.ndarray): Input image.
            psm (int): Tesseract PSM mode.

        Returns:
            str: Extracted text.
        """
        config = '-l eng --oem 3 --psm ' + str(psm)
        t = pytesseract.image_to_string(img, lang='eng', config=config)
        return t

    def box_extractor(self, img, psm):
        """Extract bounding boxes of text from an image.

        Args:
            img (numpy.ndarray): Input image.
            psm (int): Tesseract PSM mode.

        Returns:
            dict: Dictionary containing text bounding box data.
        """
        config = '-l eng --oem 3 --psm ' + str(psm)
        t = pytesseract.image_to_data(
            img, lang='eng', output_type=Output.DICT, config=config)
        return t

    def find_uid(self, text2):
        """Find possible Aadhaar UIDs from extracted text.

        Args:
            text2 (str): Extracted text.

        Returns:
            list: List of detected Aadhaar UIDs.
        """
        uid = set()
        try:
            newlist = [xx for xx in text2.split('\n') if len(xx) > 12]
            for no in newlist:
                if re.match("^[0-9 ]+$", no):
                    uid.add(no)
        except Exception:
            pass
        return list(uid)

    def is_aadhaar_card(self, text):
        """Check if the extracted text contains an Aadhaar number.

        Args:
            text (str): Extracted text.

        Returns:
            str: Aadhaar number if found, otherwise "Not Found".
        """
        res = text.split()
        aadhaar_number = ''
        for word in res:
            if len(word) == 4 and word.isdigit():
                aadhaar_number = aadhaar_number + word + ' '
        if len(aadhaar_number) >= 14:
            return aadhaar_number.strip()
        return "Not Found"
