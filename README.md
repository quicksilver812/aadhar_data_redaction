# Aadhar Data Redaction

## Overview

The Aadhar Data Redaction project is designed to automate the process of detecting and masking Aadhar card details from images and scanned documents. This ensures compliance with data privacy regulations and prevents unauthorized access to sensitive personal information.

## Features

- Detects Aadhar card details from images and scanned documents.
- Uses Optical Character Recognition (OCR) to extract text.
- Applies redaction techniques to mask sensitive data.
- Supports multiple file formats (JPG, PNG, PDF, etc.).
- Can be integrated into web-based or enterprise applications.

## Installation

### Prerequisites

- Python 3.7+
- OpenCV
- Tesseract OCR
- NumPy
- Pandas
- Matplotlib (for visualization)

### Setup Instructions

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/aadhar-data-redaction
   cd aadhar-data-redaction
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Ensure Tesseract OCR is installed:
- Linux (Ubuntu):
  ```
  sudo apt install tesseract-ocr
  ```
- Windows: Download and install from [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)

## Usage

1. Run the script with an input image or PDF:
   ```bash
   python redact.py --input path/to/image_or_pdf
   ```
2. The redacted document will be saved in the `output/` directory.

## Project Structure
```
Aadhar Data Redaction/
|-- data/                # Sample images and documents
|-- output/              # Redacted files
|-- src/
|   |-- redact.py        # Main redaction script
|   |-- ocr.py           # OCR processing module
|   |-- utils.py         # Utility functions
|-- requirements.txt     # Dependencies
|-- README.md            # Project documentation
```
## Future Enhancements

- Improve OCR accuracy using deep learning models.
- Develop a web-based UI for easier interaction.
- Enable batch processing for multiple documents.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your enhancements or bug fixes.

## License

This project is licensed under the MIT License.
