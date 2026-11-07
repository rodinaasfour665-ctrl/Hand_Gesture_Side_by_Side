# Hand Gesture Video Control — Side-by-Side Interface

This version displays **the real playing video on the left** and **your live webcam image on the right** in one desktop window. Hand landmark lines and the recognized gesture are drawn on the camera image, while a highlighted action bar describes what happened to the video. VLC handles real playback and audio.

## Windows setup

1. Install [VLC desktop](https://www.videolan.org/vlc/) (64-bit VLC for 64-bit Python).
2. Extract this ZIP to a folder and open Command Prompt/Terminal in that folder.
3. Run `python -m pip install -r requirements.txt`.
4. Copy an actual MP4 to the same folder and rename it `test.mp4`.
5. Run `python hand_gesture_video_control.py "test.mp4"`.
6. You should see **one window with two panels**. Allow webcam permission if necessary. Press `Esc` to quit.

## Actual actions

| Pose | What happens to the video |
| --- | --- |
| Open palm | Pause |
| Closed fist | Play/resume |
| Thumbs up | Increase VLC volume 10% |
| Thumbs down | Decrease VLC volume 10% |
| Victory / two fingers | Seek forward 10 seconds |
| Pointing up | Seek backward 10 seconds |

Hold a gesture steady for approximately six camera frames; to repeat the same gesture, lower your hand and make it again. The label above the status line reports the *last executed action*. The camera shows landmarks, pose name, and confidence.

## Notes

- First run downloads the MediaPipe gesture recognition model and needs internet.
- Uses a pre-trained gesture model; no training dataset is needed.
- Volume controls **the video in VLC**, not the system volume. It controls the local video opened by this app, not a browser tab.
- On Windows the video is embedded into a native Tkinter panel via VLC `set_hwnd`, rather than starting a second video window.
- The combined interface needs a real Windows/macOS/Linux desktop session and webcam; it cannot run as-is in Kaggle.
- Close other programs using your webcam before launch. If no picture appears, try `--camera 1`.
- If video is black but audio works, try switching VLC video output settings or check that VLC desktop and Python architectures match.
