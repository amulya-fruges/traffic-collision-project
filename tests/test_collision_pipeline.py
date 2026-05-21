import os
import sys
import unittest


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_ROOT = os.path.join(PROJECT_ROOT, "app")
sys.path.insert(0, APP_ROOT)

from collision_verifier import CollisionVerificationPipeline
from confidence_engine import ConfidenceEngine
from event_detector import CollisionDetector


def make_object(
    tracker_id,
    bbox,
    trajectory,
    track_age,
    speed=0,
    acceleration=0,
    direction="right",
    sudden_stop=False
):
    return {
        "tracker_id": tracker_id,
        "bbox": bbox,
        "trajectory": trajectory,
        "track_age": track_age,
        "speed": speed,
        "acceleration": acceleration,
        "direction": direction,
        "sudden_stop": sudden_stop
    }


class CollisionPipelineTests(unittest.TestCase):
    def test_kinematic_collision_is_confirmed(self):
        detector = CollisionDetector()
        verifier = CollisionVerificationPipeline.from_env()

        trajectory_a = []
        trajectory_b = []
        verified_events = []

        for frame in range(26):
            if frame < 16:
                ax1 = 80 + frame * 8
                bx1 = 340 - frame * 8
            else:
                ax1 = 208 + (frame - 16)
                bx1 = 212 - (frame - 16)

            box_a = [ax1, 100, ax1 + 90, 165]
            box_b = [bx1, 103, bx1 + 90, 168]

            center_a = ((box_a[0] + box_a[2]) // 2, (box_a[1] + box_a[3]) // 2)
            center_b = ((box_b[0] + box_b[2]) // 2, (box_b[1] + box_b[3]) // 2)
            trajectory_a.append(center_a)
            trajectory_b.append(center_b)

            impact_phase = frame >= 16

            analytics_output = [
                make_object(
                    1,
                    box_a,
                    trajectory_a,
                    track_age=frame + 1,
                    speed=8 if not impact_phase else 1,
                    acceleration=-9 if impact_phase else 0,
                    direction="right",
                    sudden_stop=impact_phase
                ),
                make_object(
                    2,
                    box_b,
                    trajectory_b,
                    track_age=frame + 1,
                    speed=8 if not impact_phase else 1,
                    acceleration=-9 if impact_phase else 0,
                    direction="left",
                    sudden_stop=impact_phase
                )
            ]

            candidates = detector.detect(analytics_output)
            verified_events.extend(verifier.verify_events(candidates))

        self.assertTrue(
            verified_events,
            "Expected kinematic collision to be verified"
        )
        self.assertTrue(verified_events[-1]["verified"])

    def test_dense_parallel_traffic_is_rejected(self):
        detector = CollisionDetector()
        verifier = CollisionVerificationPipeline.from_env()

        trajectory_a = []
        trajectory_b = []
        verified_events = []

        for frame in range(26):
            ax1 = 100 + frame * 9
            bx1 = 172 + frame * 9
            box_a = [ax1, 100, ax1 + 110, 165]
            box_b = [bx1, 105, bx1 + 110, 170]

            center_a = ((box_a[0] + box_a[2]) // 2, (box_a[1] + box_a[3]) // 2)
            center_b = ((box_b[0] + box_b[2]) // 2, (box_b[1] + box_b[3]) // 2)
            trajectory_a.append(center_a)
            trajectory_b.append(center_b)

            analytics_output = [
                make_object(
                    10,
                    box_a,
                    trajectory_a,
                    track_age=frame + 1,
                    speed=9,
                    acceleration=0,
                    direction="right",
                    sudden_stop=False
                ),
                make_object(
                    11,
                    box_b,
                    trajectory_b,
                    track_age=frame + 1,
                    speed=9,
                    acceleration=0,
                    direction="right",
                    sudden_stop=False
                )
            ]

            candidates = detector.detect(analytics_output)
            verified_events.extend(verifier.verify_events(candidates))

        self.assertEqual(
            verified_events,
            [],
            "Expected dense parallel traffic to be rejected"
        )

    def test_same_vehicle_pair_alerts_once(self):
        confidence = ConfidenceEngine()
        event = {
            "vehicle_1": 1,
            "vehicle_2": 2,
            "collision_score": 95
        }

        first = confidence.update([dict(event)])
        second = confidence.update([dict(event)])
        third = confidence.update([dict(event)])

        self.assertEqual(first, [])
        self.assertEqual(len(second), 1)
        self.assertEqual(third, [])


if __name__ == "__main__":
    unittest.main()
