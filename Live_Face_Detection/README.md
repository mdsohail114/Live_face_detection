# Live Face Mesh and Hand Tracking

A real-time webcam app built with Python, OpenCV, and MediaPipe. It draws
subtle green facial-feature outlines and a complete hand skeleton on the live
camera feed, with the current number of detected faces and hands in the
upper-left corner.

## Features

- Tracks faces and hands from a live webcam feed.
- Draws thin green outlines and sparse points for the eyes, eyebrows, nose,
  lips, and face oval, leaving the face mostly unobstructed.
- Draws all 21 landmarks and connecting lines for the palm, wrist, thumb,
  fingers, finger joints, and fingertips of up to two hands.
- Displays `Faces Detected: N` and `Hands Detected: N`.
- Mirrors the camera view and uses a 640 × 480 capture size for responsive
  tracking.
- Releases the camera and closes the tracking tasks when you press **Q**.

Face and hand tracking use MediaPipe's current Tasks API in video mode. Video
mode reuses tracking information between frames for smoother real-time
movement. The project does not identify people or analyze age or emotion.

## Python and package compatibility

The project's Python 3.14 environment is compatible with the pinned
MediaPipe 1.1.0 package and its Tasks API. The dependency
`opencv-contrib-python==4.14.0.94` provides the `cv2` module and satisfies
MediaPipe's OpenCV dependency. OpenCV 4.x is pinned because the installed
OpenCV 5.x wheel does not expose the camera/window APIs (`VideoCapture` and
`imshow`) this application uses. Do not install `opencv-python` alongside
`opencv-contrib-python`: both packages provide the same `cv2` module.

## Install and run on macOS

Open Terminal, go to the existing `Live_Face_Detection` project directory,
then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

On the first run, the app downloads the official MediaPipe face and hand
landmark model files. It stores them in the project's `models/` folder and
reuses them on later runs. An internet connection is needed for this initial
download.

## Camera permission on macOS

If macOS prompts for camera access, allow it. To check or change the setting,
open:

**System Settings → Privacy & Security → Camera**

Enable camera access for the application running Python, such as Terminal or
Visual Studio Code. If the camera does not open, check this permission, then
quit and reopen that application before trying again.

## Quit

Click the camera window and press **Q** or **q**. The program releases the
camera and closes its windows.

## Troubleshooting

- **Camera will not open:** Check the macOS camera permission above. Also
  confirm no other application is using the webcam.
- **Model download fails:** Check your internet connection and run
  `python main.py` again. The app keeps successfully downloaded models for
  future runs.
- **Package installation fails:** Confirm Python 3.14 is active in the
  virtual environment, then retry `pip install -r requirements.txt`.
- **Tracking is slow:** Close other camera-intensive applications. The app
  already requests a 640 × 480 camera feed to reduce processing work.
