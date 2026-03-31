import cv2
import mediapipe as mp

def detect_smile():
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5
    )

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        return 0, None

    ret, frame = cap.read()

    if not ret:
        cap.release()
        return 0, None

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    smile_score = 0

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0].landmark
        h, w, _ = frame.shape

        # Mouth corners
        left = landmarks[61]
        right = landmarks[291]

        # Nose reference (stable point)
        nose = landmarks[1]

        left_x = left.x * w
        right_x = right.x * w
        left_y = left.y * h
        right_y = right.y * h
        nose_y = nose.y * h

        mouth_width = abs(right_x - left_x)

        # Normalize width relative to face width
        width_ratio = mouth_width / w

        # Corner lift (smile lifts corners above neutral line)
        avg_corner_y = (left_y + right_y) / 2
        lift_amount = nose_y - avg_corner_y

        # Smile logic
        if width_ratio > 0.23 and lift_amount > 5:
            smile_score = 95
        elif width_ratio > 0.20:
            smile_score = 75
        else:
            smile_score = 40

    cap.release()

    return smile_score, frame