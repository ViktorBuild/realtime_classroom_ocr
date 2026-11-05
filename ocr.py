import cv2
import easyocr
import time

# Initialize EasyOCR reader
reader = easyocr.Reader(['en', 'ru'])

# Open webcam
cap = cv2.VideoCapture(0)

# Set initial time
prev_time = time.time()

while True:
    # Read frame from webcam
    ret, frame = cap.read()

    # Get current time
    curr_time = time.time()

    # Check if 3 seconds have elapsed
    if curr_time - prev_time >= 2:
        # Perform OCR on the frame
        results = reader.readtext(frame)
        
        for detection in results:
            text = detection[1]
            confidence = detection[2]
            
            if confidence > 0.6:
                f = open("DB.txt", 'a')
                f.write(f"{text} \n")
                print(f"{text} \n")
        # Update previous time
        prev_time = curr_time

    # Display the frame
    cv2.imshow('OCR', frame)

    # Exit if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
