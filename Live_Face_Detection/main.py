"""Real-time face mesh and hand tracking with OpenCV and MediaPipe Tasks."""

import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlretrieve

import cv2
import mediapipe as mp


PROJECT_DIR = Path(__file__).resolve().parent
MODEL_DIR = PROJECT_DIR / "models"
FACE_MODEL_PATH = MODEL_DIR / "face_landmarker.task"
HAND_MODEL_PATH = MODEL_DIR / "hand_landmarker.task"

FACE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)
HAND_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)

GREEN = (0, 255, 0)
VISION = mp.tasks.vision


def ensure_model(model_path, model_url):
    """Download a MediaPipe model once and keep it in the project models folder."""
    if model_path.is_file() and model_path.stat().st_size > 0:
        return

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    temporary_path = model_path.with_suffix(".task.download")

    try:
        print(f"Downloading {model_path.name} (only needed once)...")
        urlretrieve(model_url, temporary_path)
        temporary_path.replace(model_path)
    except (OSError, URLError) as error:
        if temporary_path.exists():
            temporary_path.unlink()
        raise RuntimeError(
            f"Could not download {model_path.name}. Check your internet "
            f"connection and try again. Details: {error}"
        ) from error


def draw_landmarks(frame, landmarks, connections, point_radius=1, thickness=1):
    """Draw normalized landmark points and their connecting lines in green."""
    height, width = frame.shape[:2]

    def pixel_position(index):
        landmark = landmarks[index]
        x = min(max(int(landmark.x * width), 0), width - 1)
        y = min(max(int(landmark.y * height), 0), height - 1)
        return x, y

    for connection in connections:
        cv2.line(
            frame,
            pixel_position(connection.start),
            pixel_position(connection.end),
            GREEN,
            thickness,
            cv2.LINE_AA,
        )

    for index in range(len(landmarks)):
        cv2.circle(
            frame,
            pixel_position(index),
            point_radius,
            GREEN,
            -1,
            cv2.LINE_AA,
        )


def draw_face_features(frame, landmarks):
    """Draw selected facial contours instead of the dense full-face mesh."""
    face_connections = VISION.FaceLandmarksConnections
    feature_groups = (
        face_connections.FACE_LANDMARKS_LEFT_EYE,
        face_connections.FACE_LANDMARKS_RIGHT_EYE,
        face_connections.FACE_LANDMARKS_LEFT_EYEBROW,
        face_connections.FACE_LANDMARKS_RIGHT_EYEBROW,
        face_connections.FACE_LANDMARKS_NOSE,
        face_connections.FACE_LANDMARKS_LIPS,
        face_connections.FACE_LANDMARKS_FACE_OVAL,
    )
    height, width = frame.shape[:2]

    for connections in feature_groups:
        # Keep the feature outlines thin and add only occasional small points.
        point_indices = sorted(
            {
                index
                for connection in connections
                for index in (connection.start, connection.end)
            }
        )
        for connection in connections:
            start = landmarks[connection.start]
            end = landmarks[connection.end]
            start_point = (
                min(max(int(start.x * width), 0), width - 1),
                min(max(int(start.y * height), 0), height - 1),
            )
            end_point = (
                min(max(int(end.x * width), 0), width - 1),
                min(max(int(end.y * height), 0), height - 1),
            )
            cv2.line(frame, start_point, end_point, GREEN, 1, cv2.LINE_AA)

        for index in point_indices[::4]:
            landmark = landmarks[index]
            point = (
                min(max(int(landmark.x * width), 0), width - 1),
                min(max(int(landmark.y * height), 0), height - 1),
            )
            cv2.circle(frame, point, 1, GREEN, -1, cv2.LINE_AA)


def create_landmarkers():
    """Create video-mode trackers that reuse tracking between camera frames."""
    face_options = VISION.FaceLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(FACE_MODEL_PATH)),
        running_mode=VISION.RunningMode.VIDEO,
        num_faces=4,
        min_face_detection_confidence=0.5,
        min_face_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    hand_options = VISION.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(HAND_MODEL_PATH)),
        running_mode=VISION.RunningMode.VIDEO,
        num_hands=2,
        min_hand_detection_confidence=0.55,
        min_hand_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return (
        VISION.FaceLandmarker.create_from_options(face_options),
        VISION.HandLandmarker.create_from_options(hand_options),
    )


def main():
    face_landmarker = None
    hand_landmarker = None
    camera = None

    try:
        # Face and hand models are downloaded from Google's official model host
        # the first time the app runs, then reused from the local models folder.
        ensure_model(FACE_MODEL_PATH, FACE_MODEL_URL)
        ensure_model(HAND_MODEL_PATH, HAND_MODEL_URL)
        face_landmarker, hand_landmarker = create_landmarkers()

        # Camera index 0 is normally the built-in or default webcam.
        camera = cv2.VideoCapture(0)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        if not camera.isOpened():
            print(
                "Error: Could not open the camera. Check macOS camera "
                "permissions for Terminal or the app running this program."
            )
            return

        print("Camera started. Press Q in the camera window to quit.")
        last_timestamp_ms = 0

        while True:
            success, frame = camera.read()
            if not success:
                print("Error: Could not read a frame from the camera.")
                break

            # Mirror the image so movement feels natural, then convert OpenCV's
            # BGR frame to the RGB format expected by MediaPipe.
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

            # VIDEO mode requires a timestamp that increases on every frame.
            timestamp_ms = max(time.monotonic_ns() // 1_000_000, last_timestamp_ms + 1)
            last_timestamp_ms = timestamp_ms

            face_result = face_landmarker.detect_for_video(mp_image, timestamp_ms)
            hand_result = hand_landmarker.detect_for_video(mp_image, timestamp_ms)

            # Draw only the main facial feature contours. This keeps the face
            # natural-looking instead of covering it with the full tessellation.
            for face in face_result.face_landmarks:
                draw_face_features(frame, face)

            # MediaPipe's 21-point hand skeleton connects the wrist, palm,
            # thumb, and all four fingers through their joints and fingertips.
            for hand in hand_result.hand_landmarks:
                draw_landmarks(
                    frame,
                    hand,
                    VISION.HandLandmarksConnections.HAND_CONNECTIONS,
                    point_radius=3,
                    thickness=2,
                )

            cv2.putText(
                frame,
                f"Faces Detected: {len(face_result.face_landmarks)}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                GREEN,
                2,
                cv2.LINE_AA,
            )
            cv2.putText(
                frame,
                f"Hands Detected: {len(hand_result.hand_landmarks)}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                GREEN,
                2,
                cv2.LINE_AA,
            )

            cv2.imshow("Live Face Mesh and Hand Tracking", frame)
            if cv2.waitKey(1) & 0xFF in (ord("q"), ord("Q")):
                break
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Error starting face and hand tracking: {error}")
    finally:
        if camera is not None:
            camera.release()
        if face_landmarker is not None:
            face_landmarker.close()
        if hand_landmarker is not None:
            hand_landmarker.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
