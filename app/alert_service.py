import cv2
import os
import json
from datetime import datetime
from pathlib import Path


class AlertService:

    def __init__(self):

        self.base_dir = (
            Path(__file__).resolve().parents[1]
        )

        self.alert_dir = (
            self.base_dir /
            "outputs" /
            "alerts"
        )

        self.log_dir = (
            self.base_dir /
            "outputs" /
            "logs"
        )

        self.screenshot_dir = (
            self.base_dir /
            "outputs" /
            "screenshots"
        )

        self.alert_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.log_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.screenshot_dir.mkdir(
            parents=True,
            exist_ok=True
        )

        self.log_file = (
            self.log_dir /
            "collision_log.json"
        )

        # Initialize empty log
        if not self.log_file.exists():

            with open(
                self.log_file,
                "w"
            ) as f:

                json.dump([], f)

    def save_screenshot(
        self,
        frame,
        event
    ):

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )

        filename = (
            f"collision_"
            f"{event['vehicle_1']}_"
            f"{event['vehicle_2']}_"
            f"{timestamp}.jpg"
        )

        path = (
            self.screenshot_dir /
            filename
        )

        cv2.imwrite(
            str(path),
            frame
        )

        return str(path)

    def append_json_log(
        self,
        log_entry
    ):

        try:

            with open(
                self.log_file,
                "r"
            ) as f:

                logs = json.load(f)

        except Exception:

            logs = []

        logs.append(log_entry)

        with open(
            self.log_file,
            "w"
        ) as f:

            json.dump(
                logs,
                f,
                indent=4
            )

    def process_alerts(
        self,
        frame,
        confirmed_events
    ):

        for event in confirmed_events:

            screenshot_path = (
                self.save_screenshot(
                    frame,
                    event
                )
            )

            timestamp = datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

            log_entry = {

                "timestamp":
                    timestamp,

                "vehicle_1":
                    event.get(
                        "vehicle_1"
                    ),

                "vehicle_2":
                    event.get(
                        "vehicle_2"
                    ),

                "collision_score":
                    event.get(
                        "collision_score"
                    ),

                "verification_score":
                    event.get(
                        "verification_score"
                    ),

                "verification_reason":
                    event.get(
                        "verification_reason"
                    ),

                "normalized_distance":
                    event.get(
                        "normalized_distance"
                    ),

                "relative_speed":
                    event.get(
                        "relative_speed"
                    ),

                "direction_a":
                    event.get(
                        "direction_a"
                    ),

                "direction_b":
                    event.get(
                        "direction_b"
                    ),

                "candidate_features":
                    event.get(
                        "candidate_features",
                        {}
                    ),

                "screenshot":
                    screenshot_path
            }

            self.append_json_log(
                log_entry
            )

            print("\n🚨 COLLISION ALERT 🚨")

            print(
                f"Vehicles: "
                f"{event['vehicle_1']} "
                f"& "
                f"{event['vehicle_2']}"
            )

            print(
                f"Collision Score: "
                f"{event.get('collision_score')}"
            )

            print(
                f"Screenshot Saved: "
                f"{screenshot_path}"
            )