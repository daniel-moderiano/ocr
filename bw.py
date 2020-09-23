import cv2

outputPath = "C:/Users/danie/Desktop/img/1_bw.jpeg"

originalImage = cv2.imread("C:/Users/danie/Desktop/img/1.jpeg")

grayImage = cv2.cvtColor(originalImage, cv2.COLOR_BGR2GRAY)

(thresh, blackAndWhiteImage) = cv2.threshold(grayImage, 180, 255, cv2.THRESH_BINARY)

cv2.imwrite(outputPath, blackAndWhiteImage)
