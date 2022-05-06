# OCR Scripts
This repository contains two Python optical character recognition (OCR) scripts for use in Optometry practice. 
* **Referral/report filing** - takes scanned PDF inputs (letters from referring practitioners, including reports, referrals, TCAs, etc) and files by patient name and +/- TCA status.
* **Humphrey Field Analyzer (HFA) test filing** - takes direct files exported by HFA and sorts tests into files by patient name, DOB, and RE/LE.

## About the project
The OCR scripts were created to try and automate certain aspect of my day-to-day administrative work in optometry practice. The referral filing script was the initial iteration of this type of script; the HFA filing script was a refined version built at a later date for use on an easier set of input data.

### Features

* **Broad range of letters can be sorted:** the referral OCR script is built to handle referrals and reports from 20+ different ophthalmologists and other health practitioners, in spite of their unique letter layout and language.
* **Error handling:** where an 'error' is encountered and the patient's name cannot be confidently deduced, the user is alerted and the file is sorted into a specified directory for manual review. This also filters spam input as a by-product.
* **Respectable accuracy:** The HFA script runs at essentially 100% accuracy as the input data is exported by a computer, resulting in a stable, consistent data set. The referral script boasts over 90% accuracy in the face of incredible input varition, both in scan quality and letter layout.

### Technologies used

The key technology used here is the Tesseract OCR - an open source OCR program with impressive capability. The Python/Windows specific version is implemented. 

* Python
* Tesseract OCR
* OpenCV for input pre-processing

## Usage

These instructions will help you set up the OCR scripts to run on your system.

> These instructions are for Windows OS. There is virtually zero presence of non-Windows OS in Optomety. 

### Installing

First, clone the repository

```
git clone git@github.com:daniel-moderiano/ocr.git
```

Inside the root directory, install the following dependencies:

```
pip install opencv-python pytesseract pyPdf4 pdf2image img2pdf
```
Tesseract OCR for Windows is also required. At time of writing, the current version is 5.0. [Poppler for Windows](blog.alivate.com.au/poppler-windows) is also required, and must be added to PATH.

From here, the input and output directories must be adjusted to your requirements. Then, the scripts can be run directly. 
> Please note the HFA script requires HFA .TIF exports and the referral script requires PDF input.

