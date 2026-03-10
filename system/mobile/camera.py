import cv2
import os
from datetime import datetime


# ---------------------------
# OPEN CAMERA PREVIEW
# ---------------------------

def open_camera():
    """
    Open webcam live preview
    Press 'q' to quit
    """
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return "❌ Camera not accessible"

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        cv2.imshow("Jarvis Camera - Press 'q' to exit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return "📷 Camera closed"


# ---------------------------
# CAPTURE PHOTO
# ---------------------------

def capture_photo(save_dir="captures"):
    """
    Capture and save a photo
    """
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return "❌ Camera not accessible"

    ret, frame = cap.read()
    cap.release()

    if not ret:
        return "❌ Failed to capture image"

    os.makedirs(save_dir, exist_ok=True)
    filename = datetime.now().strftime("photo_%Y%m%d_%H%M%S.jpg")
    path = os.path.join(save_dir, filename)

    cv2.imwrite(path, frame)
    return f"📸 Photo saved at {path}"
