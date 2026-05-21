from collections import deque
import cv2
import tempfile


class EventBuffer:

    def __init__(
        self,
        max_frames=120,
        fps=30
    ):

        self.buffer = deque(maxlen=max_frames)

        self.fps = fps

    def add_frame(self, frame):

        self.buffer.append(frame.copy())

    def export_event_clip(
        self,
        pre_frames=45,
        post_frames=45
    ):

        if len(self.buffer) < 10:
            return None

        frames = list(self.buffer)

        start = max(
            0,
            len(frames) - (
                pre_frames + post_frames
            )
        )

        selected_frames = frames[start:]

        temp_file = tempfile.NamedTemporaryFile(
            suffix=".mp4",
            delete=False
        )

        clip_path = temp_file.name

        height, width = (
            selected_frames[0].shape[:2]
        )

        writer = cv2.VideoWriter(
            clip_path,
            cv2.VideoWriter_fourcc(*"mp4v"),
            self.fps,
            (width, height)
        )

        for frame in selected_frames:
            writer.write(frame)

        writer.release()

        return clip_path