import math
from collections import defaultdict, deque


class CollisionDetector:
    """
    Advanced kinematic collision candidate detector.

    This detector avoids relying on overlap persistence alone and instead
    uses:
    - convergence analysis
    - post-impact physics
    - trajectory disturbance
    - rebound behavior
    - dense traffic suppression
    - temporal reasoning

    Designed to work before a scene-understanding verifier
    such as NVIDIA Cosmos / VSS / Video-LLaMA.
    """

    def __init__(self, verbose=False):
        self.frame_index = 0
        self.verbose = verbose

        self.pair_history = defaultdict(lambda: deque(maxlen=32))
        self.missed_pair_frames = defaultdict(int)

        self.min_history_frames = 6
        self.max_pair_missed_frames = 20
        self.min_track_age = 5

        # Adaptive proximity threshold
        self.max_near_distance = 1.65

        # Candidate threshold
        self.candidate_score_threshold = 82

        # Contact persistence
        self.close_contact_required_frames = 3

    def box_area(self, box):
        return max(1, box[2] - box[0]) * max(1, box[3] - box[1])

    def box_diag(self, box):
        return math.sqrt((box[2] - box[0]) ** 2 + (box[3] - box[1]) ** 2)

    def center(self, box):
        return (
            (box[0] + box[2]) / 2,
            (box[1] + box[3]) / 2
        )

    def center_distance(self, boxA, boxB):
        ax, ay = self.center(boxA)
        bx, by = self.center(boxB)

        return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)

    def compute_iou(self, boxA, boxB):
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interW = max(0, xB - xA)
        interH = max(0, yB - yA)

        interArea = interW * interH

        if interArea == 0:
            return 0

        boxAArea = self.box_area(boxA)
        boxBArea = self.box_area(boxB)

        return interArea / float(
            boxAArea + boxBArea - interArea
        )

    def smoothed_velocity(self, trajectory, window=6):
        if len(trajectory) < 2:
            return (0.0, 0.0)

        recent = trajectory[-window:]

        if len(recent) < 2:
            return (0.0, 0.0)

        x1, y1 = recent[0]
        x2, y2 = recent[-1]

        steps = len(recent) - 1

        return (
            (x2 - x1) / steps,
            (y2 - y1) / steps
        )

    def vector_length(self, vector):
        return math.sqrt(
            vector[0] ** 2 + vector[1] ** 2
        )

    def cosine_similarity(self, vectorA, vectorB):
        lenA = self.vector_length(vectorA)
        lenB = self.vector_length(vectorB)

        if lenA < 0.001 or lenB < 0.001:
            return 0

        return (
            vectorA[0] * vectorB[0] +
            vectorA[1] * vectorB[1]
        ) / (lenA * lenB)

    def pair_key(self, objA, objB):
        return tuple(
            sorted([
                objA["tracker_id"],
                objB["tracker_id"]
            ])
        )

    def cleanup_inactive_pairs(self, active_keys):
        for key in list(self.pair_history.keys()):

            if key in active_keys:
                self.missed_pair_frames[key] = 0
                continue

            self.missed_pair_frames[key] += 1

            if (
                self.missed_pair_frames[key]
                > self.max_pair_missed_frames
            ):
                del self.pair_history[key]
                del self.missed_pair_frames[key]

    def build_pair_sample(self, objA, objB):
        boxA = objA["bbox"]
        boxB = objB["bbox"]

        center_a = self.center(boxA)
        center_b = self.center(boxB)

        distance = self.center_distance(boxA, boxB)

        scale = max(
            1,
            (self.box_diag(boxA) + self.box_diag(boxB)) / 2
        )

        velocity_a = self.smoothed_velocity(
            objA.get("trajectory", [])
        )

        velocity_b = self.smoothed_velocity(
            objB.get("trajectory", [])
        )

        relative_velocity = (
            velocity_a[0] - velocity_b[0],
            velocity_a[1] - velocity_b[1]
        )

        pair_vector_ab = (
            center_b[0] - center_a[0],
            center_b[1] - center_a[1]
        )

        return {
            "frame_index": self.frame_index,

            "bbox_a": boxA,
            "bbox_b": boxB,

            "center_a": center_a,
            "center_b": center_b,

            "distance": distance,
            "normalized_distance": distance / scale,
            "scale": scale,

            "iou": self.compute_iou(boxA, boxB),

            "velocity_a": velocity_a,
            "velocity_b": velocity_b,

            "speed_a": self.vector_length(velocity_a),
            "speed_b": self.vector_length(velocity_b),

            "relative_speed": self.vector_length(relative_velocity),

            "motion_cosine": self.cosine_similarity(
                velocity_a,
                velocity_b
            ),

            "closing_alignment": self.cosine_similarity(
                relative_velocity,
                pair_vector_ab
            ),

            "sudden_stop":
                objA.get("sudden_stop", False) or
                objB.get("sudden_stop", False),

            "acceleration_a":
                objA.get("acceleration", 0),

            "acceleration_b":
                objB.get("acceleration", 0),

            "direction_a":
                objA.get("direction", "unknown"),

            "direction_b":
                objB.get("direction", "unknown"),

            "track_age_a":
                objA.get("track_age", 0),

            "track_age_b":
                objB.get("track_age", 0)
        }

    def has_recent_direction_change(self, samples):
        if len(samples) < 7:
            return False

        early = samples[-7]
        late = samples[-1]

        a_change = (
            self.cosine_similarity(
                early["velocity_a"],
                late["velocity_a"]
            ) < 0.25
            and late["speed_a"] > 2
        )

        b_change = (
            self.cosine_similarity(
                early["velocity_b"],
                late["velocity_b"]
            ) < 0.25
            and late["speed_b"] > 2
        )

        return a_change or b_change

    def has_speed_collapse(self, samples):
        if len(samples) < 7:
            return False

        previous = samples[-7:-2]
        current = samples[-1]

        prev_a = max(
            sample["speed_a"]
            for sample in previous
        )

        prev_b = max(
            sample["speed_b"]
            for sample in previous
        )

        collapse_a = (
            prev_a >= 5 and
            current["speed_a"] <= prev_a * 0.35
        )

        collapse_b = (
            prev_b >= 5 and
            current["speed_b"] <= prev_b * 0.35
        )

        return collapse_a or collapse_b

    def has_micro_impact(self, samples):
        """
        Detect tiny motion disturbances.
        Useful for slow close-up collisions.
        """

        if len(samples) < 8:
            return False

        recent = samples[-8:]

        def disturbance(vehicle_key):
            velocities = [
                s[vehicle_key]
                for s in recent
            ]

            directional_changes = []

            for i in range(1, len(velocities)):
                similarity = self.cosine_similarity(
                    velocities[i - 1],
                    velocities[i]
                )

                directional_changes.append(similarity)

            sudden_instability = sum(
                1
                for val in directional_changes
                if val < 0.45
            )

            return sudden_instability >= 2

        return (
            disturbance("velocity_a") or
            disturbance("velocity_b")
        )

    def has_post_impact_pause(self, samples):
        """
        Detect pause after impact.
        """

        if len(samples) < 10:
            return False

        recent = samples[-10:]

        low_motion_frames = 0

        for sample in recent[-5:]:

            if (
                sample["speed_a"] < 2.0 or
                sample["speed_b"] < 2.0
            ):
                low_motion_frames += 1

        return low_motion_frames >= 3

    def has_rebound_separation(self, samples):
        """
        Detect rebound after impact.
        """

        if len(samples) < 10:
            return False

        distances = [
            s["distance"]
            for s in samples[-10:]
        ]

        min_index = distances.index(min(distances))

        if min_index >= len(distances) - 2:
            return False

        after = distances[min_index:]

        return (
            len(after) >= 3 and
            after[-1] - after[0] > 6
        )

    def is_parallel_side_by_side(self, samples):
        """
        Suppress dense traffic flow.
        """

        recent = samples[-8:]

        if len(recent) < 5:
            return False

        motion_cosines = [
            s["motion_cosine"]
            for s in recent
        ]

        speed_diffs = [
            abs(s["speed_a"] - s["speed_b"])
            for s in recent
        ]

        distances = [
            s["distance"]
            for s in recent
        ]

        lateral_offsets = [
            abs(
                s["center_a"][1] -
                s["center_b"][1]
            )
            for s in recent
        ]

        distance_stability = (
            max(distances) - min(distances)
        ) / max(
            1,
            sum(distances) / len(distances)
        )

        lateral_stability = (
            max(lateral_offsets) -
            min(lateral_offsets)
        ) < 12

        same_motion = (
            sum(v > 0.82 for v in motion_cosines) >= 5
        )

        similar_speed = (
            sum(v < 3.5 for v in speed_diffs) >= 5
        )

        stable_spacing = distance_stability < 0.10

        return (
            same_motion and
            similar_speed and
            stable_spacing and
            lateral_stability
        )

    def score_pair(self, history):
        samples = list(history)

        current = samples[-1]

        if len(samples) < self.min_history_frames:
            return 0, {}

        if (
            current["track_age_a"] < self.min_track_age or
            current["track_age_b"] < self.min_track_age
        ):
            return 0, {
                "rejected":
                "track IDs are not stable yet"
            }

        distances = [
            sample["distance"]
            for sample in samples
        ]

        normalized_distances = [
            sample["normalized_distance"]
            for sample in samples
        ]

        recent = samples[-6:]

        recent_distances = [
            sample["distance"]
            for sample in recent
        ]

        total_distance_drop = (
            distances[0] - distances[-1]
        )

        recent_distance_drop = (
            recent_distances[0] -
            recent_distances[-1]
        )

        min_normalized_distance = min(
            normalized_distances
        )

        near_enough = (
            min_normalized_distance
            <= self.max_near_distance
        )

        approaching = (
            total_distance_drop >
            max(15, distances[0] * 0.15)
            or
            recent_distance_drop >
            max(10, recent_distances[0] * 0.12)
        )

        closing_now = (
            current["closing_alignment"] > 0.50
        )

        hard_deceleration = any(
            sample["acceleration_a"] < -6 or
            sample["acceleration_b"] < -6
            for sample in recent
        )

        sudden_stop = any(
            sample["sudden_stop"]
            for sample in recent
        )

        direction_change = (
            self.has_recent_direction_change(samples)
        )

        speed_collapse = (
            self.has_speed_collapse(samples)
        )

        micro_impact = (
            self.has_micro_impact(samples)
        )

        post_impact_pause = (
            self.has_post_impact_pause(samples)
        )

        rebound_separation = (
            self.has_rebound_separation(samples)
        )

        parallel_side_by_side = (
            self.is_parallel_side_by_side(samples)
        )

        impact_motion = (
            hard_deceleration or
            sudden_stop or
            direction_change or
            speed_collapse or
            micro_impact or
            post_impact_pause or
            rebound_separation
        )

        score = 0

        # Spatial evidence
        if near_enough:
            score += 16

        # Convergence
        if approaching:
            score += 20

        # Closing alignment
        if closing_now:
            score += 12

        # Relative speed
        if current["relative_speed"] >= 7:
            score += 12

        elif current["relative_speed"] >= 3:
            score += 8

        # Strong impact evidence
        if hard_deceleration:
            score += 18

        if sudden_stop:
            score += 16

        if speed_collapse:
            score += 20

        if direction_change:
            score += 16

        # Low-speed impact evidence
        if micro_impact:
            score += 16

        if post_impact_pause:
            score += 12

        if rebound_separation:
            score += 14

        # Penalties
        if not impact_motion:
            score -= 40

        if not approaching:
            score -= 28

        if not near_enough:
            score -= 24

        if parallel_side_by_side:
            score -= 75

        # Dense traffic suppression
        if (
            current["motion_cosine"] > 0.90 and
            abs(
                current["speed_a"] -
                current["speed_b"]
            ) < 2.5
        ):
            score -= 25

        score = max(0, min(100, score))

        features = {
            "total_distance_drop":
                round(total_distance_drop, 2),

            "recent_distance_drop":
                round(recent_distance_drop, 2),

            "min_normalized_distance":
                round(min_normalized_distance, 3),

            "near_enough":
                near_enough,

            "approaching":
                approaching,

            "closing_now":
                closing_now,

            "hard_deceleration":
                hard_deceleration,

            "sudden_stop":
                sudden_stop,

            "speed_collapse":
                speed_collapse,

            "direction_change":
                direction_change,

            "micro_impact":
                micro_impact,

            "post_impact_pause":
                post_impact_pause,

            "rebound_separation":
                rebound_separation,

            "parallel_side_by_side":
                parallel_side_by_side,

            "impact_motion":
                impact_motion,

            "history_frames":
                len(samples)
        }

        return score, features

    def detect(self, analytics_output):
        self.frame_index += 1

        collision_events = []

        active_keys = set()

        n = len(analytics_output)

        for i in range(n):

            objA = analytics_output[i]

            for j in range(i + 1, n):

                objB = analytics_output[j]

                if (
                    objA["tracker_id"] ==
                    objB["tracker_id"]
                ):
                    continue

                key = self.pair_key(objA, objB)

                active_keys.add(key)

                sample = self.build_pair_sample(
                    objA,
                    objB
                )

                history = self.pair_history[key]

                history.append(sample)

                collision_score, features = (
                    self.score_pair(history)
                )

                if (
                    collision_score <
                    self.candidate_score_threshold
                ):
                    continue

                if self.verbose:
                    print(
                        f"Collision Candidate | "
                        f"IDs: {objA['tracker_id']} "
                        f"& {objB['tracker_id']} | "
                        f"Distance: "
                        f"{sample['normalized_distance']:.3f} | "
                        f"RelSpeed: "
                        f"{sample['relative_speed']:.2f} | "
                        f"Score: {collision_score}"
                    )

                collision_events.append({
                    "vehicle_1":
                        objA["tracker_id"],

                    "vehicle_2":
                        objB["tracker_id"],

                    "iou":
                        round(sample["iou"], 3),

                    "distance":
                        round(sample["distance"], 2),

                    "normalized_distance":
                        round(
                            sample["normalized_distance"],
                            3
                        ),

                    "speed_a":
                        round(sample["speed_a"], 2),

                    "speed_b":
                        round(sample["speed_b"], 2),

                    "relative_speed":
                        round(
                            sample["relative_speed"],
                            2
                        ),

                    "direction_a":
                        sample["direction_a"],

                    "direction_b":
                        sample["direction_b"],

                    "collision_score":
                        collision_score,

                    "candidate_features":
                        features,

                    "frame_index":
                        self.frame_index
                })

        self.cleanup_inactive_pairs(active_keys)

        return collision_events