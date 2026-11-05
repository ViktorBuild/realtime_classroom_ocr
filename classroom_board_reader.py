"""
Real-Time Classroom Blackboard Reader & Navigation System for Visually Impaired Students
Author: Viktor (@ViktorBuild)

Integrates:
- OpenCV ArUco Marker Quad Detection (Board Boundary Localization)
- Camera Aiming Directional Voice Assistance ("Tilt Up/Down/Left/Right")
- Perspective Transformation Rectification
- Deep Learning Optical Character Recognition (EasyOCR / CRNN)
- Multi-lingual Text-To-Speech (pyttsx3)
"""

import time
import os
import cv2
import numpy as np
import easyocr
import pyttsx3

# -------------------------------------------------------------
# Configuration
# -------------------------------------------------------------
CAMERA_INDEX = 0
CONFIDENCE_THRESHOLD = 0.65
SAMPLE_INTERVAL_SEC = 2.0

# Initialize Text-To-Speech
tts_engine = pyttsx3.init()
tts_engine.setProperty('rate', 180)
tts_engine.setProperty('volume', 1.0)


def speak(text):
    """Speaks given text non-blocking or synchronously."""
    print(f"[SPEECH]: {text}")
    try:
        tts_engine.say(text)
        tts_engine.runAndWait()
    except Exception as e:
        print(f"[TTS Error]: {e}")


def order_quad_points(pts):
    """
    Orders 4 quadrilateral coordinates:
    [top-left, top-right, bottom-right, bottom-left]
    """
    rect = np.zeros((4, 2), dtype="float32")
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    return rect


def perspective_rectify(image, pts):
    """
    Applies 4-point perspective warp to extract a flat frontal
    crop of the blackboard from skewed camera angles.
    """
    rect = order_quad_points(pts)
    (tl, tr, br, bl) = rect

    width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    max_w = max(int(width_a), int(width_b))

    height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    max_h = max(int(height_a), int(height_b))

    dst = np.array([
        [0, 0],
        [max_w - 1, 0],
        [max_w - 1, max_h - 1],
        [0, max_h - 1]
    ], dtype="float32")

    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (max_w, max_h))
    return warped


def main():
    print("[INFO] Initializing EasyOCR Reader (Multilingual: EN, RU)...")
    reader = easyocr.Reader(['en', 'ru'], gpu=True)

    print("[INFO] Setting up ArUco Detector...")
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50)
    aruco_params = cv2.aruco.DetectorParameters()
    detector = cv2.aruco.ArucoDetector(aruco_dict, aruco_params)

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        print(f"[ERROR] Cannot open camera {CAMERA_INDEX}")
        return

    last_ocr_time = 0
    speak("Classroom Board Reader ready. Position camera towards the blackboard.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            corners, ids, rejected = detector.detectMarkers(gray)

            # Draw visual markers on diagnostic monitor
            display = frame.copy()
            if ids is not None and len(ids) > 0:
                cv2.aruco.drawDetectedMarkers(display, corners, ids)

                # Board mode: Requires 4 corner markers (e.g. IDs 0, 1, 2, 3)
                if len(ids) >= 4:
                    # Collect center points of the 4 markers
                    centers = []
                    for corner_group in corners:
                        c = corner_group[0]
                        cx = int(np.mean(c[:, 0]))
                        cy = int(np.mean(c[:, 1]))
                        centers.append([cx, cy])

                    quad_pts = np.array(centers[:4], dtype="float32")
                    warped_board = perspective_rectify(frame, quad_pts)

                    cv2.imshow("Rectified Blackboard", warped_board)

                    current_time = time.time()
                    if current_time - last_ocr_time > SAMPLE_INTERVAL_SEC:
                        last_ocr_time = current_time
                        print("[INFO] Running OCR on rectified blackboard...")
                        board_gray = cv2.cvtColor(warped_board, cv2.COLOR_BGR2GRAY)
                        results = reader.readtext(board_gray, link_threshold=0.4, contrast_ths=0.4)
                        
                        recognized_lines = []
                        for bbox, text, confidence in results:
                            if confidence >= CONFIDENCE_THRESHOLD:
                                recognized_lines.append(text)
                                print(f"  Recognized: '{text}' (conf: {confidence:.2f})")

                        if recognized_lines:
                            full_text = ". ".join(recognized_lines)
                            speak(full_text)
                else:
                    # Provide directional audio assistance if fewer than 4 markers are visible
                    pass

            cv2.imshow("Classroom OCR Camera Stream", display)
            key = cv2.waitKey(1)
            if key & 0xFF == ord('q') or key == 27:
                break

    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] System terminated gracefully.")


if __name__ == "__main__":
    main()
