import math
from collections import defaultdict, deque


class MotionAnalytics:
    """
    Advanced motion analytics layer.

    Provides:
    - smoothed speed
    - stable acceleration
    - trajectory confidence
    - motion direction
    - stationary detection
    - sudden stop detection
    - jitter suppression
    """

    def __init__(self):

        # Historical speed values
        self.velocity_history = defaultdict(
            lambda: deque(maxlen=15)
        )

        # Historical direction vectors
        self.motion_history = defaultdict(
            lambda: deque(maxlen=15)
        )

    def euclidean_distance(self, p1, p2):

        return math.sqrt(
            (p1[0] - p2[0]) ** 2 +
            (p1[1] - p2[1]) ** 2
        )

    def compute_velocity_vector(self, trajectory):

        """
        Compute smoothed motion vector.
        """

        if len(trajectory) < 3:
            return (0.0, 0.0)

        recent = trajectory[-6:]

        x1, y1 = recent[0]
        x2, y2 = recent[-1]

        steps = max(1, len(recent) - 1)

        return (
            (x2 - x1) / steps,
            (y2 - y1) / steps
        )

    def vector_length(self, vector):

        return math.sqrt(
            vector[0] ** 2 +
            vector[1] ** 2
        )

    def compute_speed(self, trajectory):

        """
        Compute stable speed estimate.
        """

        if len(trajectory) < 3:
            return 0.0

        recent = trajectory[-6:]

        distances = []

        for i in range(1, len(recent)):

            dist = self.euclidean_distance(
                recent[i - 1],
                recent[i]
            )

            distances.append(dist)

        if not distances:
            return 0.0

        # Weighted smoothing
        weighted_sum = 0
        weight_total = 0

        for idx, dist in enumerate(distances):

            weight = idx + 1

            weighted_sum += dist * weight
            weight_total += weight

        return weighted_sum / weight_total

    def compute_acceleration(
        self,
        tracker_id,
        speed
    ):

        """
        Smoothed acceleration estimate.
        """

        history = self.velocity_history[tracker_id]

        history.append(speed)

        if len(history) < 4:
            return 0.0

        recent = list(history)[-4:]

        diffs = []

        for i in range(1, len(recent)):
            diffs.append(
                recent[i] - recent[i - 1]
            )

        return sum(diffs) / len(diffs)

    def compute_direction(self, vector):

        """
        Convert motion vector to direction label.
        """

        dx, dy = vector

        magnitude = self.vector_length(vector)

        if magnitude < 1.0:
            return "stationary"

        angle = math.degrees(
            math.atan2(dy, dx)
        )

        if -45 <= angle < 45:
            return "right"

        elif 45 <= angle < 135:
            return "down"

        elif angle >= 135 or angle < -135:
            return "left"

        else:
            return "up"

    def compute_motion_stability(
        self,
        tracker_id,
        velocity_vector
    ):

        """
        Measure consistency of motion.
        Useful for micro-impact detection.
        """

        history = self.motion_history[tracker_id]

        history.append(velocity_vector)

        if len(history) < 5:
            return 1.0

        similarities = []

        recent = list(history)[-5:]

        for i in range(1, len(recent)):

            v1 = recent[i - 1]
            v2 = recent[i]

            len1 = self.vector_length(v1)
            len2 = self.vector_length(v2)

            if len1 < 0.001 or len2 < 0.001:
                continue

            cosine = (
                v1[0] * v2[0] +
                v1[1] * v2[1]
            ) / (len1 * len2)

            similarities.append(cosine)

        if not similarities:
            return 1.0

        return sum(similarities) / len(similarities)

    def detect_sudden_stop(
        self,
        speed,
        acceleration
    ):

        """
        Detect realistic sudden stopping.
        """

        return (
            speed > 4 and
            acceleration < -4.5
        )

    def detect_stationary_state(self, speed):

        return speed < 1.2

    def analyze(self, tracked_objects):

        analytics_output = []

        for obj in tracked_objects:

            tracker_id = obj["tracker_id"]

            trajectory = obj["trajectory"]

            velocity_vector = (
                self.compute_velocity_vector(
                    trajectory
                )
            )

            speed = self.compute_speed(
                trajectory
            )

            acceleration = (
                self.compute_acceleration(
                    tracker_id,
                    speed
                )
            )

            direction = self.compute_direction(
                velocity_vector
            )

            motion_stability = (
                self.compute_motion_stability(
                    tracker_id,
                    velocity_vector
                )
            )

            sudden_stop = (
                self.detect_sudden_stop(
                    speed,
                    acceleration
                )
            )

            stationary = (
                self.detect_stationary_state(
                    speed
                )
            )

            analytics_output.append({

                "tracker_id":
                    tracker_id,

                "bbox":
                    obj["bbox"],

                "trajectory":
                    trajectory,

                "track_age":
                    obj.get("track_age", 0),

                "velocity_vector":
                    velocity_vector,

                "speed":
                    round(speed, 3),

                "acceleration":
                    round(acceleration, 3),

                "direction":
                    direction,

                "motion_stability":
                    round(motion_stability, 3),

                "sudden_stop":
                    sudden_stop,

                "stationary":
                    stationary
            })

        return analytics_output