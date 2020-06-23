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

input_dir = "C:/Users/OptosAdmin/Desktop/fields_test"
output_dir = "C:/Users/OptosAdmin/Desktop/fields_test/output"


def extract_name_from_list(a_list):
    if "DOB:" in a_list:
        a_list.pop()
        a_list.pop()

    return("-".join(a_list).lower())

def extract_prefix_from_name(name_string):
    prefixes = ["-mrs", "-mr", "-miss", "-master", "-ms"]
    for prefix in prefixes:
        if prefix in name_string:
            name_string = name_string.replace(("-" + prefix), "")

    return name_string

def extract_invalid_characters(a_string):
    name_string_cleaned = a_string
    invalid_chars = "*+=?"
    for i in invalid_chars:
        if i in a_string:
            name_string_cleaned = a_string.replace(i, "")

    return name_string_cleaned

def erase_xml(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if ".xml" in file:
                os.remove(os.path.join(root, file))

def erase_txt(path):
    for root, dirs, files in os.walk(path):
        for file in files:
            if ".txt" in file:
                os.remove(os.path.join(root, file))

def ocr_reader(input_path, output_path):
    for file in os.listdir(input_path):
           
        if Path(file).suffix == '.tif':
            full_name = input_path + "/" + file         
            test_date = file[4:12]    

            if file[20:22] == "OD":
                test_eye = "RE"
            else:
                test_eye = "LE"

            outfile = os.path.join(output_path, (file + "_out_text.txt"))

            f = open(outfile, "a")
            text = str(((pytesseract.image_to_string(Image.open(full_name)))))
            text = text.replace('-\n', '')
            f.write(text)
            f.close()

            f = open(outfile, 'r')
            output_list = []
            dob_list = []
            for line in f:
                values = line.split()

                if 'Name:' in values:
                    output_list = values[1:]
                
                if "DOB:" in values:
                    dob_list = values

            px_name_base = extract_name_from_list(output_list)
            patient_name = extract_prefix_from_name(px_name_base)
            dob = (dob_list.pop()).replace("-", "")

            test_name = patient_name + "_" + test_eye + "_" + test_date
            save_path = os.path.join(output_dir, (patient_name + "_" + dob))

            try:
                if not os.path.exists(save_path):
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
