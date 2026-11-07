"""Control a REAL local video using webcam hand gestures.

Requires: pip install -r requirements.txt AND VLC desktop application.
Run: python hand_gesture_video_control.py "path/to/video.mp4"
Press Q in the camera window to quit.
"""

import argparse
import time
import urllib.request
from pathlib import Path

import cv2
import mediapipe as mp

try:
    import vlc
except (ImportError, OSError) as exc:
    raise SystemExit(
        "VLC is required. Install the VLC desktop application and run "
        "'python -m pip install -r requirements.txt'."
    ) from exc

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/"
    "gesture_recognizer/float16/1/gesture_recognizer.task"
)
MODEL_PATH = Path(__file__).with_name("gesture_recognizer.task")

# MediaPipe's built-in gesture names (no additional training required).
GESTURE_ACTIONS = {
    "Open_Palm": "Pause video",
    "Closed_Fist": "Play video",
    "Thumb_Up": "Volume +10",
    "Thumb_Down": "Volume -10",
    "Victory": "Forward 10 seconds",
    "Pointing_Up": "Back 10 seconds",
}
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),
]


def ensure_model():
    if not MODEL_PATH.exists():
        print("Downloading gesture recognition model (first run)...")
        try:
            urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        except Exception as error:
            MODEL_PATH.unlink(missing_ok=True)
            raise RuntimeError("Could not download model; check internet.") from error
    return str(MODEL_PATH)


def draw_landmarks(frame, landmarks):
    height, width = frame.shape[:2]
    points = [(int(p.x * width), int(p.y * height)) for p in landmarks]
    for start, end in HAND_CONNECTIONS:
        cv2.line(frame, points[start], points[end], (25, 200, 90), 2)
    for point in points:
        cv2.circle(frame, point, 3, (255, 255, 255), -1)


def perform_action(player, gesture):
    """Change actual VLC playback, audio volume or position."""
    if gesture == "Open_Palm":
        player.set_pause(1)
    elif gesture == "Closed_Fist":
        if not player.is_playing():
            # Resume paused VLC playback or start if it hasn't begun yet.
            player.play()
    elif gesture in ("Thumb_Up", "Thumb_Down"):
        volume = player.audio_get_volume()
        if volume < 0:
            return "Volume unavailable"
        change = 10 if gesture == "Thumb_Up" else -10
        player.audio_set_volume(max(0, min(100, volume + change)))
    elif gesture in ("Victory", "Pointing_Up"):
        current_ms = player.get_time()
        if current_ms < 0 or not player.is_seekable():
            return "Seeking unavailable"
        change_ms = 10000 if gesture == "Victory" else -10000
        target_ms = max(0, current_ms + change_ms)
        duration_ms = player.get_length()
        if duration_ms > 0:
            target_ms = min(target_ms, duration_ms)
        player.set_time(target_ms)
    return GESTURE_ACTIONS[gesture]


def main():
    """One Tkinter window: VLC video on the left, live camera on the right."""
    import sys
    import tkinter as tk
    from tkinter import ttk
    from PIL import Image, ImageTk

    parser = argparse.ArgumentParser(description="Real video + webcam, side by side")
    parser.add_argument("video", type=Path, help="Path to local video, e.g. test.mp4")
    parser.add_argument("--camera", type=int, default=0)
    args = parser.parse_args()
    video = args.video.expanduser().resolve()
    if not video.is_file():
        parser.error(f"Video file not found: {video}")

    model_path = ensure_model()
    camera = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW) if sys.platform == "win32" else cv2.VideoCapture(args.camera)
    if not camera.isOpened():
        raise RuntimeError("Cannot open webcam. Check permissions / other camera apps.")

    root = tk.Tk()
    root.title("Hand Gesture Video Controller | Video + Live Camera")
    root.geometry("1280x750")
    root.minsize(900, 550)
    root.configure(bg="#131824")
    root.protocol("WM_DELETE_WINDOW", lambda: close())

    title = tk.Label(root, text="HAND GESTURE  |  REAL VIDEO CONTROL", fg="white",
                     bg="#131824", font=("Segoe UI", 18, "bold"))
    title.pack(pady=(13, 5))

    panels = tk.Frame(root, bg="#131824")
    panels.pack(fill="both", expand=True, padx=14, pady=10)
    panels.grid_columnconfigure(0, weight=1, uniform="panels")
    panels.grid_columnconfigure(1, weight=1, uniform="panels")
    panels.grid_rowconfigure(1, weight=1)
    tk.Label(panels, text="VIDEO PLAYER", bg="#131824", fg="#d8e2f1",
             font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))
    tk.Label(panels, text="LIVE CAMERA + HAND LANDMARKS", bg="#131824", fg="#d8e2f1",
             font=("Segoe UI", 12, "bold")).grid(row=0, column=1, sticky="w", pady=(0, 8))

    video_side = tk.Frame(panels, bg="black", highlightbackground="#334155", highlightthickness=2)
    video_side.grid(row=1, column=0, sticky="nsew", padx=(0, 6))
    cam_side = tk.Frame(panels, bg="#050505", highlightbackground="#334155", highlightthickness=2)
    cam_side.grid(row=1, column=1, sticky="nsew", padx=(6, 0))

    # VLC renders inside this Tkinter native widget, rather than a separate window.
    video_surface = tk.Frame(video_side, bg="black")
    video_surface.pack(fill="both", expand=True)
    cam_label = tk.Label(cam_side, bg="black")
    cam_label.pack(fill="both", expand=True)

    action_var = tk.StringVar(value="Ready — hold a hand gesture in front of the camera")
    action_label = tk.Label(root, textvariable=action_var, bg="#1e293b", fg="#7dd3fc",
                            font=("Segoe UI", 15, "bold"), anchor="center", pady=10)
    action_label.pack(fill="x", padx=14)

    status_var = tk.StringVar(value="Loading video...")
    tk.Label(root, textvariable=status_var, bg="#131824", fg="#e5e7eb",
             font=("Segoe UI", 11)).pack(pady=6)
    tk.Label(root, text="PALM: Pause    FIST: Play    THUMB UP/DOWN: Volume +/-10    "
             "VICTORY: +10 sec    POINTING UP: -10 sec    ESC: Quit",
             bg="#131824", fg="#9ca3af", font=("Segoe UI", 10)).pack(pady=(0, 12))

    root.update_idletasks()
    root.update()
    try:
        instance = vlc.Instance("--no-video-title-show")
        player = instance.media_player_new()
        # Set the target window BEFORE starting playback.
        if sys.platform == "win32":
            player.set_hwnd(video_surface.winfo_id())
        elif sys.platform == "darwin":
            player.set_nsobject(video_surface.winfo_id())
        else:
            player.set_xwindow(video_surface.winfo_id())
        player.set_media(instance.media_new(str(video)))
        player.play()
        player.audio_set_volume(50)
    except Exception as error:
        camera.release()
        root.destroy()
        raise RuntimeError("VLC could not start inside the app. Check VLC desktop installation.") from error

    options = mp.tasks.vision.GestureRecognizerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
        running_mode=mp.tasks.vision.RunningMode.VIDEO,
        num_hands=1,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6,
    )
    try:
        recognizer = mp.tasks.vision.GestureRecognizer.create_from_options(options)
    except Exception:
        camera.release()
        player.stop()
        root.destroy()
        raise

    state = {"running": True, "candidate": None, "frames": 0,
             "last_gesture": None, "last_at": 0., "last_action": "None",
             "started": time.monotonic(), "timestamp": -1, "picture": None}

    def close():
        if not state["running"]:
            return
        state["running"] = False
        camera.release()
        recognizer.close()
        player.stop()
        root.destroy()

    root.bind("<Escape>", lambda _event: close())

    def update_frame():
        if not state["running"]:
            return
        ok, frame = camera.read()
        if not ok:
            action_var.set("Camera frame unavailable — check webcam connection")
            root.after(250, update_frame)
            return

        frame = cv2.flip(frame, 1)
        image = mp.Image(image_format=mp.ImageFormat.SRGB,
                         data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        timestamp = max(state["timestamp"] + 1,
                        int((time.monotonic() - state["started"]) * 1000))
        state["timestamp"] = timestamp
        result = recognizer.recognize_for_video(image, timestamp)
        gesture, confidence = "None", 0.0
        if result.hand_landmarks:
            draw_landmarks(frame, result.hand_landmarks[0])
        if result.gestures and result.gestures[0]:
            top = result.gestures[0][0]
            gesture, confidence = top.category_name, top.score

        if gesture == state["candidate"]:
            state["frames"] += 1
        else:
            state["candidate"], state["frames"] = gesture, 1
        if gesture not in GESTURE_ACTIONS or confidence < 0.65:
            state["last_gesture"] = None
        elif (state["frames"] >= 6 and gesture != state["last_gesture"]
              and time.monotonic() - state["last_at"] >= 0.8):
            action = perform_action(player, gesture)
            state["last_action"] = action
            state["last_gesture"] = gesture
            state["last_at"] = time.monotonic()
            action_var.set(f"{gesture.replace('_', ' ')}  →  {action.upper()}")
            print(f"{gesture}: {action}")

        # Draw the gesture label and confidence directly on the CAMERA image.
        h, w = frame.shape[:2]
        cv2.rectangle(frame, (0, 0), (w, 72), (15, 23, 42), -1)
        cv2.putText(frame, f"GESTURE: {gesture.replace('_', ' ')}", (12, 27),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(frame, f"Confidence: {confidence:.0%}", (12, 57),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (120, 220, 255), 2, cv2.LINE_AA)

        # Keep camera feed contained within the right-hand video panel.
        target_w, target_h = max(2, cam_label.winfo_width()), max(2, cam_label.winfo_height())
        scale = min(target_w / w, target_h / h)
        new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
        resized = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)
        picture = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)))
        cam_label.configure(image=picture)
        cam_label.image = picture  # Prevent Tk from garbage collecting the image.

        duration = player.get_length()
        position = player.get_time()
        mmss = lambda millis: f"{max(0, millis)//60000:02d}:{(max(0, millis)//1000)%60:02d}"
        status = "PLAYING" if player.is_playing() else "PAUSED"
        status_var.set(f"VIDEO: {status}    {mmss(position)} / {mmss(duration)}    "
                       f"VOLUME: {max(0, player.audio_get_volume())}%")
        root.after(30, update_frame)

    root.after(100, update_frame)
    try:
        root.mainloop()
    finally:
        if state["running"]:
            close()


if __name__ == "__main__":
    main()
