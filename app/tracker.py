from collections import defaultdict, deque
import os
import warnings
import math

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

import supervision as sv
import numpy as np


class VehicleTracker:

    def __init__(self):

        # ByteTrack tracker
        with warnings.catch_warnings():

            warnings.filterwarnings(
                "ignore",
                category=FutureWarning,
                message=".*ByteTrack.*"
            )

            self.tracker = sv.ByteTrack()

        # Historical trajectories
        self.trajectories = defaultdict(
            lambda: deque(maxlen=40)
        )

        # Historical bbox centers
        self.center_history = defaultdict(
            lambda: deque(maxlen=12)
        )

        # Historical bbox sizes
        self.size_history = defaultdict(
            lambda: deque(maxlen=12)
        )

        # Track age
        self.track_ages = defaultdict(int)

        # Lost track counters
        self.lost_counts = defaultdict(int)

        # Minimum detection confidence
        self.min_detection_confidence = 0.35

        # Maximum center jitter allowed
        self.max_jitter_threshold = 35

    def euclidean_distance(self, p1, p2):

        return math.sqrt(
            (p1[0] - p2[0]) ** 2 +
            (p1[1] - p2[1]) ** 2
        )

    def smooth_center(self, tracker_id, center):

        """
        Smooth noisy bbox center movement.
        """

        history = self.center_history[tracker_id]

        history.append(center)

        recent = list(history)

        if len(recent) < 3:
            return center

        xs = [p[0] for p in recent]
        ys = [p[1] for p in recent]

        smooth_x = int(sum(xs) / len(xs))
        smooth_y = int(sum(ys) / len(ys))

        return (smooth_x, smooth_y)

    def compute_bbox_stability(
        self,
        tracker_id,
        width,
        height
    ):

        """
        Detect unstable bounding boxes.
        """

        history = self.size_history[tracker_id]

        history.append((width, height))

        if len(history) < 5:
            return 1.0

        widths = [w for w, h in history]
        heights = [h for w, h in history]

        width_var = np.std(widths)
        height_var = np.std(heights)

        instability = width_var + height_var

        return max(
            0.0,
            1.0 - (instability / 50.0)
        )

    def is_jittering_track(
        self,
        tracker_id
    ):

        """
        Detect unstable jittering tracks.
        """

        history = self.center_history[tracker_id]

        if len(history) < 6:
            return False

        recent = list(history)[-6:]

        jumps = []

        for i in range(1, len(recent)):

            dist = self.euclidean_distance(
                recent[i - 1],
                recent[i]
            )

            jumps.append(dist)

        if not jumps:
            return False

        jump_variation = np.std(jumps)

        return (
            jump_variation >
            self.max_jitter_threshold
        )

    def cleanup_lost_tracks(
        self,
        active_track_ids
    ):

        for tracker_id in list(self.track_ages.keys()):

            if tracker_id in active_track_ids:

                self.lost_counts[tracker_id] = 0
                continue

            self.lost_counts[tracker_id] += 1

            # Remove stale tracks
            if self.lost_counts[tracker_id] > 30:

                if tracker_id in self.trajectories:
                    del self.trajectories[tracker_id]

                if tracker_id in self.center_history:
                    del self.center_history[tracker_id]

                if tracker_id in self.size_history:
                    del self.size_history[tracker_id]

                del self.track_ages[tracker_id]
                del self.lost_counts[tracker_id]

    def update(self, detections, frame):

        if len(detections) == 0:
            return []

        xyxy = []
        confidences = []
        class_ids = []

        # Filter weak detections
        for det in detections:

            if (
                det["confidence"] <
                self.min_detection_confidence
            ):
                continue

            xyxy.append(det["bbox"])

            confidences.append(
                det["confidence"]
            )

            class_ids.append(
                det["class_id"]
            )

        if len(xyxy) == 0:
            return []

        detections_sv = sv.Detections(
            xyxy=np.array(
                xyxy,
                dtype=np.float32
            ),

            confidence=np.array(
                confidences,
                dtype=np.float32
            ),

            class_id=np.array(
                class_ids,
                dtype=np.int32
            )
        )

        tracked = (
            self.tracker.update_with_detections(
                detections_sv
            )
        )

        tracked_objects = []

        active_track_ids = set()

        for i in range(len(tracked.xyxy)):

            x1, y1, x2, y2 = map(
                int,
                tracked.xyxy[i]
            )

            tracker_id = int(
                tracked.tracker_id[i]
            )

            active_track_ids.add(tracker_id)

            width = x2 - x1
            height = y2 - y1

            raw_center = (
                int((x1 + x2) / 2),
                int((y1 + y2) / 2)
            )

            # Smooth center trajectory
            smooth_center = self.smooth_center(
                tracker_id,
                raw_center
            )

            # Track age
            self.track_ages[tracker_id] += 1

            # Store trajectory
            self.trajectories[tracker_id].append(
                smooth_center
            )

            # Compute bbox stability
            bbox_stability = (
                self.compute_bbox_stability(
                    tracker_id,
                    width,
                    height
                )
            )

            # Reject highly unstable tracks
            if bbox_stability < 0.25:
                continue

            # Detect jitter
            jittering = (
                self.is_jittering_track(
                    tracker_id
                )
            )

            tracked_objects.append({

                "tracker_id":
                    tracker_id,

                "bbox":
                    [x1, y1, x2, y2],

                "trajectory":
                    list(
                        self.trajectories[
                            tracker_id
                        ]
                    ),

                "track_age":
                    self.track_ages[
                        tracker_id
                    ],

                "class_id":
                    int(
                        tracked.class_id[i]
                    ),

                "confidence":
                    float(
                        tracked.confidence[i]
                    ),

                "bbox_stability":
                    round(
                        bbox_stability,
                        3
                    ),

                "jittering":
                    jittering
            })

        self.cleanup_lost_tracks(
            active_track_ids
        )

        return tracked_objects