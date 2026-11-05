import cv2
from cv2 import aruco
import easyocr
import pyttsx3
import time
import keyboard

engine = pyttsx3.init()
engine.setProperty('rate', 200)  # Adjust the speaking rate (words per minute)
engine.setProperty('volume', 1)  # Adjust the volume (0.0 to 1.0)
engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_RU-RU_IRINA_11.0')

def perform_ocr(image):
    result = reader.readtext(image, decoder = "greedy", canvas_size = 250, link_threshold = 0.4, contrast_ths = 0.4)
    for detection in result:
        text = detection[1]
        confidence = detection[2]
        if confidence > 0.7:
            engine.say(text)
            engine.runAndWait()
            print(f'Text: {text}, Confidence: {confidence}')



def find_list(a, b):  # function that checks if the needed AruCo ID is in the list
    for x in a:
        if x == b:
            return True
    return False

def clean_list(compare_list, destination_set):
    cleaned = []
    for x in destination_set:
        for y in range(len(compare_list)):
            if x == compare_list[y]:
                cleaned.append(x)
    return cleaned


# Initialize EasyOCR reader
reader = easyocr.Reader(['ru'])  # Specify the languages you want to support (e.g., English)

# Capture video from the webcam
video_capture = cv2.VideoCapture(1)

# Set the time interval for sampling (2 seconds)
sample_interval = 1
last_sample_time = time.time()



lang = 0  # RUS - 0 | KAZ - 1
mode = 0  # BOARD - 0 | NAVIGATION - 1
room = 1  # TOILET - 0 | CANTEEN - 1







if not room: # TOILET
    destination_set = {5, 6, 7, 8}
    destination_dict = {5: "Forward.mp3",
                        6: "LTurn.mp3",
                        7: "Forward.mp3",
                        8: "Stop.mp3"}
else: # CANTEEN
    destination_set = {9, 10, 11, 12}
    destination_dict = {9: "RTurn.mp3",
                        10: "Forward.mp3",
                        11: "LTurn.mp3",
                        12: "Stop.mp3"}
compare_set = set({})
cv2.namedWindow("OKNO", cv2.WINDOW_NORMAL)
if lang:  # path to the mp3
    path = "C:/Users/Viktor/Desktop/BBC/KAZ/"
else:
    path = "C:/Users/Viktor/Desktop/BBC/RUS/"

dict_aruco = aruco.Dictionary_get(aruco.DICT_5X5_250)  # defining type of AruCo marker
parameters = aruco.DetectorParameters_create()

cap = cv2.VideoCapture(2)  # ID of camera

try:
    while True:
        ret, frame = cap.read()  # Getting videostream from camera
        gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)
        ids = []
        cleanID = []
        corners, ids, rejectedImgPoints = aruco.detectMarkers(gray, dict_aruco,
                                                              parameters=parameters)  # getting ID of markers and their coordinates
        # print(ids)
        try:
            # print("try")
            for ID in ids:  # getting list of IDs in list format
                cleanID.append(ID[0])
            if not mode:  # board mode
                #print("board")
                counter = []
                for x in range(1, 5):  # checking IDs of board's markers
                    counter.append(find_list(cleanID, x))
                if counter[0] and counter[1] and counter[2] and counter[3]:  # the board is fully visible
                    print("You see the full board")
                    for ID in ids:  # getting list of IDs in list format
                        cleanID.append(ID[0])
                    coord_dict = {cleanID[0] : corners[0][0],
                                  cleanID[1] : corners[1][0],
                                  cleanID[2] : corners[2][0],
                                  cleanID[3] : corners[3][0]
                                  }
                    
                    x1 = int(coord_dict[1][2][0])
                    y1 = int(coord_dict[1][2][1])
                    x2 = int(coord_dict[4][0][0])
                    y2 = int(coord_dict[4][0][1])
                    # Crop image
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    crop_img = frame[y1:y2, x1:x2]

                    if not mode:  # board mode
                        #print("board")
                        counter = []
                        for x in range(1, 5):  # checking IDs of board's markers
                            counter.append(find_list(cleanID, x))
                        
                        # Check if it's time to perform OCR
                    current_time = time.time()
                    elapsed_time = current_time - last_sample_time
                    if elapsed_time >= sample_interval:
                        last_sample_time = current_time

                            # Perform OCR on the captured frame
                        gray = cv2.cvtColor(crop_img, cv2.COLOR_BGR2GRAY)
                        perform_ocr(gray)

                    if not counter[0] and not counter[1] and not counter[2] and not counter[3]:
                        break
                    
                    f = open("sound.txt", "w")
                    f.write("0")
                    f = f.close()
                elif counter[0] and counter[1] and not counter[2] and not counter[3]:  # look up!
                    sound = "Down.mp3"
                    f = open("sound.txt", "w")
                    f.write(path + sound)
                    f = f.close()
                elif not counter[0] and not counter[1] and counter[2] and counter[3]:  # look down!
                    sound = "Up.mp3"
                    f = open("sound.txt", "w")
                    f.write(path + sound)
                    f = f.close()
                elif not counter[0] and counter[1] and not counter[2] and counter[3]:  # look left!
                    sound = "Left.mp3"
                    f = open("sound.txt", "w")
                    f.write(path + sound)
                    f = f.close()
                elif counter[0] and not counter[1] and counter[2] and not counter[3]:  # look right!
                    sound = "Right.mp3"
                    f = open("sound.txt", "w")
                    f.write(path + sound)
                    f = f.close()
                else:
                    f = open("sound.txt", "w")
                    f.write("0")
                    f = f.close()
            else:  # navigation mode
                for ID in cleanID:
                    compare_set.add(ID) # getting set of markers' ids
                compare_list = list(compare_set)
                compare_list = clean_list(compare_list, destination_set) # cleaning list from ids that we don't need
                if len(compare_list):
                    #print(destination_dict[compare_list[-1]])
                    f = open("sound.txt", "w")
                    f.write(path + destination_dict[compare_list[-1]]) # path to the audio
                    f = f.close()
        except Exception:
            print("no markers")
            f = open("sound.txt", "w")
            f.write("0")
            f = f.close()
        frame_markers = aruco.drawDetectedMarkers(frame.copy(), corners, ids)
        cv2.imshow('OKNO', frame_markers)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        elif cv2.waitKey(1) & 0xFF == ord('z'):
            engine.say("Режим изменен")
            engine.runAndWait()
            mode = 1 - mode
        elif cv2.waitKey(1) & 0xFF == ord('x'):
            engine.say("Язык изменен")
            engine.runAndWait()
            lang = 1 - lang
            if lang:  # path to the mp3
                path = "C:/Users/Viktor/Desktop/BBC/KAZ/"
            else:
                path = "C:/Users/Viktor/Desktop/BBC/RUS/"
    cv2.destroyWindow('frame')
    cap.release()
except KeyboardInterrupt:
    cv2.destroyWindow('frame')
    cap.release()
