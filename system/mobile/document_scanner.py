import cv2
import os
import numpy as np
from datetime import datetime


# ---------------------------
# SCAN DOCUMENT
# ---------------------------

def scan_document(save_dir="scans"):
    """
    Scan a document using webcam
    Press 's' to scan, 'q' to quit
    """
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return "❌ Camera not accessible"

    os.makedirs(save_dir, exist_ok=True)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        display = frame.copy()
        cv2.putText(display, "Press 'S' to Scan | 'Q' to Quit",
                    (10, 30), cv2.FONT_HERSHEY_SIMPLEX,
                    0.7, (0, 255, 0), 2)

        cv2.imshow("Jarvis Document Scanner", display)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('s'):
            scanned = process_document(frame)
            filename = datetime.now().strftime("scan_%Y%m%d_%H%M%S.jpg")
            path = os.path.join(save_dir, filename)
            cv2.imwrite(path, scanned)
            cap.release()
            cv2.destroyAllWindows()
            return f"📄 Document scanned and saved at {path}"

        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return "📄 Document scanner closed"


# ---------------------------
# PROCESS DOCUMENT IMAGE
# ---------------------------

def process_document(image):
    """
    Convert image to scanned style
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    scanned = cv2.adaptiveThreshold(
        blur, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )
    return scanned
