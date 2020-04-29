from PIL import Image
import string
import pytesseract
import sys
import os
import pathlib
from pathlib import Path
from pdf2image import convert_from_path
from PyPDF4 import PdfFileReader, PdfFileWriter
import shutil
import cv2
import numpy as np


admin_dir = "C:/Users/Daniel/Documents/Programming/admin"
output_dir = "C:/Users/Daniel/Documents/Programming/admin/ocr_output"

prefixes = ["RE:", "Re:", "Regarding:", "RE;", "Re;", "Regarding;", 'Mr', 'MR', 'Mrs', 'MRS', 'Ms', 'MS', 'Miss', 'MISS', 'Master', 'MASTER']

identifiers = ['Mr', 'MR', 'Mrs', 'MRS', 'Ms', 'MS', 'Miss', 'MISS', 'Master', 'MASTER']

valid_chars = string.ascii_letters + "'"


#TODO improve print functions to be able to (hopefully) allow better understanding of errors to aid review.



# noise removal
def remove_noise(image):
    return cv2.medianBlur(image,5)

#opening - erosion followed by dilation
def opening(image):
    kernel = np.ones((5,5),np.uint8)
    return cv2.morphologyEx(image, cv2.MORPH_OPEN, kernel)


def pre_process(image):
    
    denoise = remove_noise(image)

    return denoise


def list_refinement(input_list):
    output_list = []
    starters = ["RE:", "Re:", "RE;", "Re;"]
    if len(input_list) > 1:
        for a_list in input_list:
            if len(a_list) > 2:
                output_list.append(a_list)
    else:
        output_list = input_list

    for i in output_list:
        if starters[0] in i or starters[1] in i or starters[2] in i or starters[3] in i:
            output_list = i
            break

        else:
            for item in identifiers:
                if item in i and i.index(item) == 0:
                    output_list = i
 
    return output_list
    



def tca_removal(input_list):
    output_list = []
    
    if "Team" in input_list and "Care" in input_list:
        try:
            output_list = input_list[(input_list.index("Arrangements") + 2):]
        except ValueError:
            separator = "_"
            report = separator.join(input_list)
            print("Error in identifying the word 'Arrangements' in file" + report + ", defaulted to 'for', but be aware there may be read errors.")
            output_list = input_list[(input_list.index("for") + 1):]

    else:
        output_list = input_list

    return output_list


def name_list_creator(file_line):
    flag = ['RE:', 'Re:', "RE;", "Re;"]

    for item in file_line:
        if item in flag:
            file_line.remove(item)

    return file_line


def prefix_remover(input_list, identifier_list):
    for item in input_list:
        if item in identifier_list:
            input_list.remove(item)
    

    return input_list


def invalid_char_remover(input_list, valid_string):
    output_list = []

    for item in input_list:
        for char in item:
            if char not in valid_string:
                item = item.replace(char, "")

        output_list.append(item)

    
    return output_list


def invalid_item_remover(input_list):
    #use this function to isolate the item 'dob' or 'DOB' and remove it, as well as remove empty spaces and any irrelevant information coming after the DOB tag
    for item in input_list:
        # With poorer quality files 'DOB' can be interpreted as 'OOB' or 'DDB' or 'ODB' hence these are included
        if item == 'dob' or item == 'DOB' or item == 'OOB' or item == 'DDB' or item == 'ODB':
            input_list = input_list[:(input_list.index(item))]
    
    #Sometimes "DOB" will not be recognised, and so the above line will fail. We should be able to use a similar algorithm for returning the list prior to the first index of a blank space.

    for item in input_list:
        if item == '':
            input_list = input_list[:(input_list.index(item))]
            break 

    return input_list


def reverse_capitalise(input_list):
    output_list = []
    if len(input_list) < 2 or len(input_list) > 3:
        
        pass
    elif len(input_list) == 2:
        for item in input_list:
            output_list.append(item.capitalize())
        output_list.reverse()

    else:
        input_list.insert(0, input_list.pop())
        for item in input_list:
            output_list.append(item.capitalize())

    return output_list

def list_to_string(list_from_file):
    output_1 = name_list_creator(list_from_file)
    output_2 = prefix_remover(output_1, identifiers)
    output_3 = invalid_char_remover(output_2, valid_chars)
    output_4 = invalid_item_remover(output_3)
    output_5 = reverse_capitalise(output_4)
    
    # With the function that takes the returned value, we should include an exception for when the 'None' value is received from this function, and display the error message outlined below. 
    final_name = "_".join(output_5)  

    return final_name


def ocr_reader(input_path, output_path):
    tca = False
    #Initialise file count to separate different ocr_outputs
    file_id = 1

    #Generate the individual path for each PDF in a particular directory "input_path".
    for file in os.listdir(input_path):
       
        letter_date = "_" + file[0:6]
        #This lists all files in the input_path dir at time of running. Most notably in doesn't search subdirectories so will not loop when new files are created in this function.           
        if Path(file).suffix == '.pdf':
            full_name = input_path + "/" + file

            #An adjustment to the pdf2image function. The following grans the max pages from the file and processes them in batches of 10, as well as utilising an output folder to prevent memory errors. 
            pdf_images = convert_from_path(full_name, dpi=500, fmt='jpg', output_folder=(output_dir))

            #Counter to store images of each page of the pdf_images list
            image_counter = 1

            #Iterate through all the pages stored in the pdf_images variable above
            for page in pdf_images:

                #Declaring filename for each page as a PNG file page 1 -> page_1.png and outputting to the designated output file path "output"
                filename = os.path.join(output_path, ("pdf_" + file + "_page_")) + str(image_counter) + ".jpg"
                
                #Save the image of the page in the system
                page.save(filename, format='JPEG')

                #Run a pre-processing module on the saved images and re-save them
                img = cv2.imread(filename)
                
                cv2.imwrite(filename, pre_process(img))
                
                #Increment the counter to update filename
                image_counter = image_counter + 1

            #Variable to get count of total number of pages
            filelimit = image_counter - 1

            #Create a test file to write the output. Associate with the file current in iteration loop with file_count variable
            outfile = os.path.join(output_path, ("pdf" + str(file_id) + "_out_text.txt"))

            #Open the file in append mode so that all contents of all images for that file are added to the same output file.
            f = open(outfile, "a")

            #Iterate from 1 to the total number of pages
            for i in range(1, filelimit + 1):

                #Set filename to recognise text from each individual page from the file currently in iteration.
                filename = os.path.join(output_path, ("pdf_" + file + "_page_")) + str(i) + ".jpg"

                #Read the text using pytesseract
                text = str(((pytesseract.image_to_string(Image.open(filename)))))

                #Write the text
                text = text.replace('-\n', '')
                f.write(text)
                
            
            f.close()

            
            #Update the file_id variable to separate files
            file_id = file_id + 1
            f = open(outfile, 'r')
            output_list = []
            for line in f:
                values = line.split()
                for i in prefixes:
                    if i in values:
                        if values not in output_list:
                            output_list.append((values))
                if "Team" in values and "Care" in values:
                    tca = True
                                                                                                                            
            if output_list != []:
                
                refined_list = list_refinement(output_list)
                refined_list_2 = tca_removal(refined_list)

                try:
                    final_refinement = list_to_string(refined_list_2)
                
                except AttributeError:
                    print("Error occurred with file " + file + ". Unable to correctly identify 'Re:' prefix or line starting with 'Mr/Mrs/etc'.")
                    shutil.move(full_name, admin_dir + "/review/" + file)
         
                else:
                    new_filename = final_refinement
                    if new_filename == "":
                        print(file + " has encountered an error, no file name generated")
                        shutil.move(full_name, admin_dir + "/review/" + file)

                    else:
                        if tca:
                            # Be aware there is the potential for mistakes in the file name is a PDF is provided without a letter date. 
                            complete_filename = new_filename + "_tca" + letter_date
                        else:
                            complete_filename = new_filename + letter_date
                        old_filepath = full_name
                        save_dir_path = os.path.join(output_dir, (new_filename))

                        
                   
                        
                        if not os.path.exists(save_dir_path):
                            os.makedirs(save_dir_path)

                        file_filepath = os.path.join(save_dir_path, (complete_filename + ".pdf"))

                        #Renames first instance of duplicate with _01 suffix, however for continued duplicates
                        if os.path.exists(file_filepath):
                            try:
                                file_filepath = file_filepath.replace(".pdf", "_01.pdf")
                                os.rename(old_filepath, file_filepath)

                            except FileExistsError:
                                print("Error occurred with file " + file + ", multiple duplicates detected, please review manually")
                                shutil.move(full_name, admin_dir + "/review/" + complete_filename + ".pdf")

                        else:
                            os.rename(old_filepath, file_filepath)

                        print("File created for {}".format(new_filename) + ", from " + file) 

                finally:
                    tca = False
            
            else:
                print("Unable to locate any identifiers in " + file + ". Please review manually.")
                shutil.move(full_name, admin_dir + "/review/" + file)


def eraser(output_path):
    for root, dirs, files in os.walk(output_path):
        for file in files:
            if ".jpg" in file or '.txt' in file:
                os.remove(os.path.join(root, file))


def main():
    ocr_reader(admin_dir, output_dir)
    eraser(output_dir)


if __name__ == "__main__":
    main()
