from PIL import Image
import string
import pytesseract
import sys
import os
import pathlib
from pathlib import Path
import shutil
import numpy as np
import cv2

# Define input directory where current (unfiled) files are stored
input_dir = "C:/Users/TestUser/Fields"

# Sorted files will be saved to this directory
output_dir = "B:/Fields"

# Removes the 'DOB' label from the 'DOB: 01/01/2001' format date string
def extract_name_from_list(a_list):
    if "DOB:" in a_list:
        a_list.pop()
        a_list.pop()

    return("-".join(a_list).lower())

# Remove prefix from patient's name
def extract_prefix_from_name(name_string):
    prefixes = ["-mrs", "-mr", "-miss", "-master", "-ms"]
    for prefix in prefixes:
        if prefix in name_string:
            name_string = name_string.replace(prefix, "")

    return name_string

# Remove any invalid characters from the patient's name (these are not permitted in file names when saving new files)
def extract_invalid_characters(a_string):
    name_string_cleaned = a_string
    invalid_chars = "*+=?"
    for i in invalid_chars:
        if i in a_string:
            name_string_cleaned = a_string.replace(i, "")

    return name_string_cleaned

# Remove unneccessary xml files from input directory (always packaged alongside TIF field files)
def erase_xml(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if ".xml" in file:
                os.remove(os.path.join(root, file))

# Remove unneccessary txt files from input directory (always packaged alongside TIF field files
def erase_txt(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if ".txt" in file:
                os.remove(os.path.join(root, file))

# The central function to 'read' visual field files and extract the patient's name/DOB for filing
def ocr_reader(input_path, output_path):
    # Iterate each file in the input directory
    for file in os.listdir(input_path):
           
        if Path(file).suffix == '.tif':   # Visual fields are exported in TIF format
            full_name = input_path + "/" + file         
            test_date = file[4:12]    # extract test date directly from file name

            # Determine which eye the test is for (is in original filename by default)
            if file[20:22] == "OD":
                test_eye = "RE"
            elif file[20:22] == "OS":
                test_eye = "LE"
            else: 
                test_eye = "OU"

            # Create a text file output containing the OCR data read from the TIF files
            outfile = os.path.join(output_path, (file + "_out_text.txt"))

            f = open(outfile, "a")
            text = str(((pytesseract.image_to_string(Image.open(full_name)))))
            text = text.replace('-\n', '')
            f.write(text)
            f.close()

            # Open the OCR-created text file and extract the name and DOB lines
            f = open(outfile, 'r')
            output_list = []
            dob_list = []
            for line in f:
                values = line.split()

                if 'Name:' in values:
                    output_list = values[1:]
                
                if "DOB:" in values:
                    dob_list = values

            # Run Name/DOB strings through custom filtering functions
            px_name_base = extract_name_from_list(output_list)
            patient_name_clean = extract_invalid_characters(px_name_base)
            patient_name = extract_prefix_from_name(patient_name_clean)
            patient_name = extract_prefix_from_name(px_name_base)
            dob = (dob_list.pop()).replace("-", "")

            # Create the final file name for the resulting file, and save
            test_name = patient_name + "_" + test_date + "_" + test_eye 
            save_path = os.path.join(output_dir, (patient_name + "_" + dob))

            try:
                if not os.path.exists(save_path):   # Create new directory if noe does not exist
                    os.makedirs(save_path)
                
                shutil.move(full_name, os.path.join(save_path, (test_name + ".tif")))
                print(patient_name, "successfully filed")
            except OSError:
                print("Error occurred with file " + file + ". Please review")
                shutil.move(full_name, input_path + "/review/" + file)

        else:
            continue


def main():
    ocr_reader(input_dir, output_dir)
    erase_xml(input_dir)
    erase_txt(output_dir)
    
    print("All tests sorted")

if __name__ == "__main__":
    main()
