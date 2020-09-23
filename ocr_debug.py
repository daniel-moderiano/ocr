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
import numpy as np
import cv2
import time
import datetime
# pip install the following: opencv-python, pytesseract, pyPdf4, pdf2image
# Also requires tesseract ocr install for Windows 5.0


#Current directories mostly for testing, these should be adjusted to suit your individual needs depending on system.
admin_dir = "C:/Users/danie/Desktop/admin"
output_dir = "C:/Users/danie/Desktop/admin/ocr-output"

#List and string variables containing the key strings that the OCR will search for in articles. Although we might use prefixes[...] instead of 2 separate lists, the separation makes things simpler. 
prefixes = ["RE:", "Re:", "Regarding:", "RE;", "Re;", "Regarding;", 'Mr', 'MR', 'Mrs', 'MRS', 'Ms', 'MS', 'Miss', 'MISS', 'Master', 'MASTER']
identifiers = ['Mr', 'MR', 'Mrs', 'MRS', 'Ms', 'MS', 'Miss', 'MISS', 'Master', 'MASTER', 'Regarding:']
valid_chars = string.ascii_letters + "'"

#Define the OpenCV noise removal function used for pre-processing. All faxes will be provided in grayscale. Further pre-processing is shown so far to increase error rate. 
def remove_noise(image):
    return cv2.medianBlur(image,5)

#Following is a collection of functions that take the input from tesseract OCR (text file) and use the above identifier lists to locate and refine the text to patient name only.

#Key list refinement function. Input is either a single list or nested list, one of which should contain the patient's name. Function aims to identify and separate this list.
def list_refinement(input_list):
    output_list = []
    starters = ["RE:", "Re:", "RE;", "Re;"]
    if len(input_list) > 1:
        for a_list in input_list:
            #The appropriate list must have length > 2 as it should have an identifier and the patient name. Hence all invalid lists are not appended here.
            if len(a_list) > 2:
                output_list.append(a_list)
    else:
        output_list = input_list

    #At this stage we either have a single or nested list, one (or more) of which contains the patient's name. This step identifies the first list that fits this criteria with the starters or identifiers. Note the patient name is likely to be early in the text, so the first valid list is most appropriate to choose. Preference is toward starters as being the identifier with name prefixes as a fall-back.
    for i in output_list:
        if starters[0] in i or starters[1] in i or starters[2] in i or starters[3] in i:
            output_list = i
            break

        elif "DOB:" in i:
            output_list = i
            break

        else:
            for item in identifiers:
                if item in i and i.index(item) == 0:
                    output_list = i
 
    #Occasionally there is poor input and no appropriate list will be generated by this function. This will later return an AttributeError in a subsequent function. Typically this means no starters were found or the identifier was not at the beginning of a line. Usually this results from poor file quality
    return output_list
    


#Many files contain the string "Re: Team Care Arrangments for Mr/Mrs ....". This function removes the leading string with the TCA terms.
def tca_removal(input_list):
    output_list = []
    
    if "Team" in input_list and "Care" in input_list:
        #A fallback in case the word "Arrangments" is not read correctly. This usually means poor file quality, hence the error message advises manual review for further errors. This should prevent the script breaking, though a possibility still exists if "for" is not read. However, if 'Team' and 'Care' are both read successfully, it seems unlikely to have issues with both 'Arrangements' and 'for'.
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

#Simply removes the identifier from the input list, leaving patient name and any following terms.
def name_list_creator(file_line):
    identifier = ['RE:', 'Re:', "RE;", "Re;" "Regarding:", "Regarding;"]

    for item in file_line:
        if item in identifier:
            start = file_line.index(item)
            file_line = file_line[start:]
            file_line.remove(item)

    return file_line

#Removes any Mr/Mrs/etc terms preceding the patient name. This list could be re-defined within this function and would likely aid simplicity.
def prefix_remover(input_list, identifier_list):
    for item in input_list:
        if item in identifier_list:
            input_list.remove(item)
    
    if input_list[0][0] not in valid_chars:
        input_list = input_list[1:]

    return input_list

#A function to remove all numbers and other innappropriate characters using the originally defined list at start of file. Note this removes the date of birth from many files (the intended target of this function).
def invalid_char_remover(input_list, valid_string):
    output_list = []
    for item in input_list:
        for char in item:
            if char not in valid_string:
                item = item.replace(char, "")

        output_list.append(item)
    
    return output_list


 #This function isolates the item 'dob' or 'DOB' and removes it, as well as removes empty spaces and any irrelevant information coming after the DOB tag.
def invalid_item_remover(input_list):
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

#Convert any combination of patient name capitalisation and order into Lastname_Firstname format (handles middle names as well as Lastname_Firstname_Middlename). This function also passes names with one term or >3 terms, as this may be an error, or an especially long name requiring review. Have not encountered such an error yet so I have not seen it's handling. 
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

#A combination of all the refinement functions above. It is not the most ideal setup but it does the job and returns a single string in the form noted for the reverse_capitalise funciton note.
def list_to_string(list_from_file):
    output_1 = name_list_creator(list_from_file)
    print("From name_list_creator:", output_1)
    output_2 = prefix_remover(output_1, identifiers)
    print("From prefix_remover:", output_2)
    output_3 = invalid_char_remover(output_2, valid_chars)
    print("From invalid_char_remover:", output_3)
    output_4 = invalid_item_remover(output_3)
    print("From invalid_item_remover:", output_4)
    output_5 = reverse_capitalise(output_4)
    print("From reverse_capitalise:", output_5)
    final_name = "_".join(output_5)  
    print("From final_name:", final_name)

    return final_name


#The meat of the script.
def ocr_reader(input_path, output_path):
    #Initialise the tca variable.
    tca = False
    #Initialise file count to separate different ocr_outputs
    file_id = 1

    #Generate the individual path for each PDF in a particular directory "input_path".
    for file in os.listdir(input_path):       
        letter_date = "_" + file[0:6]
        #This lists all files in the input_path dir at time of running. Most notably in doesn't search subdirectories so will not loop when new files are created in this function.           
        if Path(file).suffix == '.pdf':
            date = time.ctime(os.path.getctime(admin_dir + "/" + file))
            mod = (os.path.getmtime(admin_dir + "/" + file))
            modctime = time.ctime(os.path.getmtime(admin_dir + "/" + file))
            print(datetime.datetime.fromtimestamp(mod))
            # print("Created: {}".format(date))
            print("Last modified: {}".format(modctime))
            full_name = input_path + "/" + file

            #An adjustment to the pdf2image function that utilises an output folder to prevent memory errors. 
            pdf_images = convert_from_path(full_name, dpi=500, fmt='jpg', output_folder=(output_dir))

            #Counter to store images of each page of the pdf_images list
            image_counter = 1

            #Iterate through all the pages stored in the pdf_images variable above
            for page in pdf_images:

                #Declaring filename for each page as a PNG file page 1 -> page_1.png and outputting to the designated output file path "output"
                filename = os.path.join(output_path, ("pdf_" + file + "_page_")) + str(image_counter) + ".jpg"
                
                #Save the image of the page in the system
                page.save(filename, format='JPEG')

                #Run a pre-processing module on the saved images by reading them, reducing noise, then re-saving them
                img = cv2.imread(filename)
                cv2.imwrite(filename, remove_noise(img))
                
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

            #Re-open the text file generate by OCR and read line-by-line
            f = open(outfile, 'r')
            output_list = []
            for line in f:
                values = line.split()

                #The following uses the prefixes listed in the variable top of file to identify the line in the output file that contains or most likely contains the patient name. This line is then fed to the refinement functions to isolate the patient name. 
                for i in prefixes:
                    if i in values:
                        if values not in output_list:
                            output_list.append((values))

                
                #An additional classifier to identify team care arrangments. The tca variable is later referred to when determining whether to append 'tca' to the file name.
                if "Team" in values and "Care" in values:
                    tca = True

            #Check that the initial search of the OCR output file was able to find any identifier strings                                                                                                       
            if output_list != []:
                print("List direct from file:", output_list)
                #Perform refinement functions.
                refined_list = list_refinement(output_list)
                print("Refined list 1:", refined_list)

                refined_list_2 = tca_removal(refined_list)
                print("Refined list 2:", refined_list_2)

                #Error handling for the case where an appropriate list cannot be found after the first list_refinement function (see notes for this function for details)
                try:
                    final_refinement = list_to_string(refined_list_2)
                
                except AttributeError:
                    print("Error occurred with file " + file + ". Unable to correctly identify 'Re:' prefix or line starting with 'Mr/Mrs/etc'.")

                    #Key feature to move all failed files into a directory for easy review
                    shutil.move(full_name, admin_dir + "/review/" + file)
         
                #If the refinement is successful, and a filename is able to be generated, then the pdf file is sorted and named into a directory under the patient's name. Otherwise it is again sorted to the review directory.
                else:
                    new_filename = final_refinement
                    if new_filename == "":
                        print(file + " has encountered an error, no file name generated")
                        shutil.move(full_name, admin_dir + "/review/" + file)

                    else:

                        #Append tca to the file name if the file is found to be a TCA
                        if tca:

                            #Be aware there is the potential for mistakes in the file name is a PDF is provided without a letter date. 
                            complete_filename = new_filename + "_tca" + letter_date

                        else:
                            complete_filename = new_filename + letter_date
                            
                        old_filepath = full_name
                        save_dir_path = os.path.join(output_dir, (new_filename))

                        #Simple check for duplicate files, if not then proceed with the write.                                    
                        if not os.path.exists(save_dir_path):
                            os.makedirs(save_dir_path)

                        file_filepath = os.path.join(save_dir_path, (complete_filename + ".pdf"))

                        #Handling of duplicates. This will rename the first instance of a duplicate with _01 suffix, however for continued duplicates the handling shifts to moving files into the review folder. This is done because it is extremely unlikely that a single patient will ever see multiple faxes with original material sent on the same date. It is likely a true error or multiple sending of the same file, hence it should be treated as an error. If a continued duplicate numbering system was used these errors would go unnoticed.
                        if os.path.exists(file_filepath):
                            try:
                                file_filepath = file_filepath.replace(".pdf", "_01.pdf")
                                os.rename(old_filepath, file_filepath)

                            except FileExistsError:
                                print("Error occurred with file " + file + ", multiple duplicates detected, please review manually")
                                shutil.move(full_name, admin_dir + "/review/" + complete_filename + ".pdf")

                        else:
                            os.rename(old_filepath, file_filepath)

                        #Final print function allows us to review patient names for errors. This requires simple manual review and spotting unusual spellings or similar. Error prone but simply no way to automate outside of using a dictionary of known names to highlight those that seem abnormal. Diminished return for coding that I believe however.
                        print("File created for {}".format(new_filename) + ", from " + file) 

                #Make sure regardless the tca variable is reset to false.
                finally:
                    tca = False
            
            #The error message that identifies where the initial text file did not contain the identifiers.
            else:
                print("Unable to locate any identifiers in " + file + ". Please review manually.")
                shutil.move(full_name, admin_dir + "/review/" + file)

#Removes all jpg and txt files created during the proess of running the ocr_reader function.
def eraser(output_path):
    for root, dirs, files in os.walk(output_path):
        for file in files:
            if ".jpg" in file or '.txt' in file:
                os.remove(os.path.join(root, file))

#Final function and input to ensure window doesn't immediately close.
def main():
    ocr_reader(admin_dir, output_dir)
    eraser(output_dir)

if __name__ == "__main__":
    main()

input("Press ENTER to exit")
