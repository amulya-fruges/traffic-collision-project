# import cv2
# import os

# from pathlib import Path

# from detector import TrafficDetector

# from tracker import VehicleTracker

# from analytics import MotionAnalytics

# from event_detector import CollisionDetector

# from collision_verifier import (
#     CollisionVerificationPipeline,
#     SceneUnderstandingVerifier
# )

# from confidence_engine import ConfidenceEngine

# from alert_service import AlertService

# from event_buffer import EventBuffer


# BASE_DIR = (
#     Path(__file__).resolve().parents[1]
# )

# OUTPUT_VIDEO_DIR = (
#     BASE_DIR /
#     "outputs" /
#     "processed_videos"
# )

# OUTPUT_VIDEO_DIR.mkdir(
#     parents=True,
#     exist_ok=True
# )


# # -----------------------------------
# # Initialize Modules
# # -----------------------------------

# detector = TrafficDetector(
#     model_path=str(
#         BASE_DIR /
#         "models" /
#         "yolo11l.pt"
#     ),
#     conf_threshold=0.4
# )

# tracker = VehicleTracker()

# analytics_engine = MotionAnalytics()

# collision_detector = CollisionDetector()

# collision_verifier = (
#     CollisionVerificationPipeline(
#         verifier=SceneUnderstandingVerifier()
#     )
# )

# confidence_engine = ConfidenceEngine()

# alert_service = AlertService()


# # -----------------------------------
# # Video Input
# # -----------------------------------

# VIDEO_PATH = os.getenv(
#     "VIDEO_PATH",
#     str(
#         BASE_DIR /
#         "sample_videos" /
#         "crash.mp4"
#     )
# )

# MAX_FRAMES = int(
#     os.getenv("MAX_FRAMES", "0")
# )

# cap = cv2.VideoCapture(
#     VIDEO_PATH
# )


# if not cap.isOpened():

#     print("❌ Error opening video.")

#     exit()


# # -----------------------------------
# # Video Writer
# # -----------------------------------

# width = int(
#     cap.get(
#         cv2.CAP_PROP_FRAME_WIDTH
#     )
# )

# height = int(
#     cap.get(
#         cv2.CAP_PROP_FRAME_HEIGHT
#     )
# )

# fps = int(
#     cap.get(
#         cv2.CAP_PROP_FPS
#     )
# )

# if fps == 0:
#     fps = 30

# event_buffer = EventBuffer(
#     fps=fps
# )

# fourcc = cv2.VideoWriter_fourcc(
#     *"mp4v"
# )

# out = cv2.VideoWriter(
#     str(
#         OUTPUT_VIDEO_DIR /
#         "output.mp4"
#     ),
#     fourcc,
#     fps,
#     (width, height)
# )

# print(
#     "\n🚀 Starting Traffic Collision Pipeline...\n"
# )


# # -----------------------------------
# # Main Loop
# # -----------------------------------

# frame_count = 0

# while True:

#     ret, frame = cap.read()

#     if not ret:
#         break

#     frame_count += 1

#     if (
#         MAX_FRAMES
#         and
#         frame_count > MAX_FRAMES
#     ):
#         break

#     # Store frame in temporal buffer
#     event_buffer.add_frame(frame)

#     # --------------------------------
#     # Detection
#     # --------------------------------

#     detections = detector.detect(
#         frame
#     )

#     # --------------------------------
#     # Tracking
#     # --------------------------------

#     tracked_objects = tracker.update(
#         detections,
#         frame
#     )

#     # --------------------------------
#     # Motion Analytics
#     # --------------------------------

#     analytics_output = (
#         analytics_engine.analyze(
#             tracked_objects
#         )
#     )

#     # --------------------------------
#     # Collision Detection
#     # --------------------------------

#     collision_candidates = (
#         collision_detector.detect(
#             analytics_output
#         )
#     )

#     # --------------------------------
#     # Cosmos Verification
#     # --------------------------------

#     collision_events = []

#     for candidate in collision_candidates:

#         clip_path = (
#             event_buffer.export_event_clip()
#         )

#         verified = (
#             collision_verifier.verifier.verify(
#                 candidate,
#                 frame=frame,
#                 clip_path=clip_path
#             )
#         )

#         if verified.get("verified"):

#             collision_events.append(
#                 verified
#             )

#     # --------------------------------
#     # Confidence Engine
#     # --------------------------------

#     confirmed_events = (
#         confidence_engine.update(
#             collision_events
#         )
#     )

#     # --------------------------------
#     # Alerts
#     # --------------------------------

#     alert_service.process_alerts(
#         frame,
#         confirmed_events
#     )

#     # --------------------------------
#     # Visualization
#     # --------------------------------

#     for obj in analytics_output:

#         x1, y1, x2, y2 = obj["bbox"]

#         tracker_id = obj["tracker_id"]

#         speed = round(
#             obj["speed"],
#             1
#         )

#         direction = obj["direction"]

#         cv2.rectangle(
#             frame,
#             (x1, y1),
#             (x2, y2),
#             (0, 255, 0),
#             2
#         )

#         cv2.putText(
#             frame,
#             f"ID {tracker_id} | "
#             f"Speed {speed} | "
#             f"{direction}",
#             (x1, y1 - 10),
#             cv2.FONT_HERSHEY_SIMPLEX,
#             0.5,
#             (0, 255, 0),
#             2
#         )

#         trajectory = obj["trajectory"]

#         for point in trajectory:

#             cv2.circle(
#                 frame,
#                 point,
#                 3,
#                 (255, 0, 0),
#                 -1
#             )

#     # --------------------------------
#     # Collision Visualization
#     # --------------------------------

#     for event in confirmed_events:

#         cv2.putText(
#             frame,
#             "COLLISION DETECTED",
#             (50, 50),
#             cv2.FONT_HERSHEY_SIMPLEX,
#             1,
#             (0, 0, 255),
#             3
#         )

#         cv2.putText(
#             frame,
#             f"Vehicles: "
#             f"{event['vehicle_1']} "
#             f"& "
#             f"{event['vehicle_2']}",
#             (50, 90),
#             cv2.FONT_HERSHEY_SIMPLEX,
#             0.8,
#             (0, 0, 255),
#             2
#         )

#         cv2.putText(
#             frame,
#             f"Hybrid Score: "
#             f"{event['hybrid_score']}",
#             (50, 130),
#             cv2.FONT_HERSHEY_SIMPLEX,
#             0.8,
#             (0, 0, 255),
#             2
#         )

#         cv2.rectangle(
#             frame,
#             (0, 0),
#             (width, 160),
#             (0, 0, 255),
#             3
#         )

#         # Print Cosmos reasoning
#         print("\n====================")
#         print("COLLISION VERIFIED")
#         print("====================")

#         print(
#             f"\nScene Summary:\n"
#             f"{event.get('scene_summary', '')}"
#         )

#         print(
#             f"\nReason:\n"
#             f"{event.get('verification_reason', '')}"
#         )

#         print(
#             f"\nFault Estimation:\n"
#             f"{event.get('fault_estimation', '')}"
#         )

#         print(
#             f"\nEvidence:\n"
#             f"{event.get('evidence', [])}"
#         )

#     # --------------------------------
#     # Frame Counter
#     # --------------------------------

#     cv2.putText(
#         frame,
#         f"Frame: {frame_count}",
#         (20, height - 20),
#         cv2.FONT_HERSHEY_SIMPLEX,
#         0.6,
#         (255, 255, 255),
#         2
#     )

#     # --------------------------------
#     # Save Output
#     # --------------------------------

#     out.write(frame)


# # -----------------------------------
# # Cleanup
# # -----------------------------------

# cap.release()

# out.release()

# cv2.destroyAllWindows()

# print("\n✅ Processing Complete")

# print(
#     "\n🎥 Output Video Saved:\n"
#     f"{OUTPUT_VIDEO_DIR / 'output.mp4'}"
# )



import cv2
import os

from pathlib import Path

from detector import TrafficDetector

from tracker import VehicleTracker

from analytics import MotionAnalytics

from event_detector import CollisionDetector

from collision_verifier import (
    CollisionVerificationPipeline,
    LocalKinematicVerifier
)

from confidence_engine import ConfidenceEngine

from alert_service import AlertService


BASE_DIR = (
    Path(__file__).resolve().parents[1]
)

OUTPUT_VIDEO_DIR = (
    BASE_DIR /
    "outputs" /
    "processed_videos"
)

OUTPUT_VIDEO_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# -----------------------------------
# Initialize Modules
# -----------------------------------

detector = TrafficDetector(
    model_path=str(
        BASE_DIR /
        "models" /
        "yolo11l.pt"
    ),
    conf_threshold=0.4
)

tracker = VehicleTracker()

analytics_engine = MotionAnalytics()

collision_detector = CollisionDetector()

collision_verifier = (
    CollisionVerificationPipeline(
        verifier=LocalKinematicVerifier()
    )
)

confidence_engine = ConfidenceEngine()

alert_service = AlertService()


# -----------------------------------
# Video Input
# -----------------------------------

VIDEO_PATH = os.getenv(
    "VIDEO_PATH",
    str(
        BASE_DIR /
        "sample_videos" /
        "non_crash2.mp4"
    )
)

MAX_FRAMES = int(
    os.getenv("MAX_FRAMES", "0")
)

cap = cv2.VideoCapture(
    VIDEO_PATH
)

if not cap.isOpened():

    print("❌ Error opening video.")

    exit()


# -----------------------------------
# Video Writer
# -----------------------------------

width = int(
    cap.get(
        cv2.CAP_PROP_FRAME_WIDTH
    )
)

height = int(
    cap.get(
        cv2.CAP_PROP_FRAME_HEIGHT
    )
)

fps = int(
    cap.get(
        cv2.CAP_PROP_FPS
    )
)

if fps == 0:
    fps = 30

fourcc = cv2.VideoWriter_fourcc(
    *"mp4v"
)

out = cv2.VideoWriter(
    str(
        OUTPUT_VIDEO_DIR /
        "output.mp4"
    ),
    fourcc,
    fps,
    (width, height)
)

print(
    "\n🚀 Starting Traffic Collision Pipeline...\n"
)


# -----------------------------------
# Main Loop
# -----------------------------------

frame_count = 0

while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_count += 1

    if (
        MAX_FRAMES
        and
        frame_count > MAX_FRAMES
    ):
        break

    # --------------------------------
    # Detection
    # --------------------------------

    detections = detector.detect(
        frame
    )

    # --------------------------------
    # Tracking
    # --------------------------------

    tracked_objects = tracker.update(
        detections,
        frame
    )

    # --------------------------------
    # Motion Analytics
    # --------------------------------

    analytics_output = (
        analytics_engine.analyze(
            tracked_objects
        )
    )

    # --------------------------------
    # Collision Detection
    # --------------------------------

    collision_candidates = (
        collision_detector.detect(
            analytics_output
        )
    )

    # --------------------------------
    # Verification
    # --------------------------------

    collision_events = (
        collision_verifier.verify_events(
            collision_candidates,
            frame=frame
        )
    )

    # --------------------------------
    # Confidence Engine
    # --------------------------------

    confirmed_events = (
        confidence_engine.update(
            collision_events
        )
    )

    # --------------------------------
    # Alerts
    # --------------------------------

    alert_service.process_alerts(
        frame,
        confirmed_events
    )

    # --------------------------------
    # Visualization
    # --------------------------------

    for obj in analytics_output:

        x1, y1, x2, y2 = obj["bbox"]

        tracker_id = obj["tracker_id"]

        speed = round(
            obj["speed"],
            1
        )

        direction = obj["direction"]

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        cv2.putText(
            frame,
            f"ID {tracker_id} | "
            f"Speed {speed} | "
            f"{direction}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (0, 255, 0),
            2
        )

        trajectory = obj["trajectory"]

        for point in trajectory:

            cv2.circle(
                frame,
                point,
                3,
                (255, 0, 0),
                -1
            )

    # --------------------------------
    # Collision Visualization
    # --------------------------------

    for event in confirmed_events:

        cv2.putText(
            frame,
            "COLLISION DETECTED",
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            3
        )

        cv2.putText(
            frame,
            f"Vehicles: "
            f"{event['vehicle_1']} "
            f"& "
            f"{event['vehicle_2']}",
            (50, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

        cv2.putText(
            frame,
            f"Score: "
            f"{event['collision_score']}",
            (50, 130),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 0, 255),
            2
        )

        cv2.rectangle(
            frame,
            (0, 0),
            (width, 160),
            (0, 0, 255),
            3
        )

        print("\n====================")
        print("COLLISION VERIFIED")
        print("====================")

        print(
            f"\nVehicles: "
            f"{event['vehicle_1']} "
            f"& "
            f"{event['vehicle_2']}"
        )

        print(
            f"\nCollision Score: "
            f"{event['collision_score']}"
        )

        print(
            f"\nReason: "
            f"{event['verification_reason']}"
        )

    # --------------------------------
    # Frame Counter
    # --------------------------------

    cv2.putText(
        frame,
        f"Frame: {frame_count}",
        (20, height - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    # --------------------------------
    # Save Output
    # --------------------------------

    out.write(frame)


# -----------------------------------
# Cleanup
# -----------------------------------

cap.release()

out.release()

cv2.destroyAllWindows()

print("\n✅ Processing Complete")

print(
    "\n🎥 Output Video Saved:\n"
    f"{OUTPUT_VIDEO_DIR / 'output.mp4'}"
)