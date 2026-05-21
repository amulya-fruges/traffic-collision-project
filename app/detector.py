import cv2
import os

os.environ.setdefault("YOLO_CONFIG_DIR", "/tmp/Ultralytics")
os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")

from ultralytics import YOLO

# Traffic-focused COCO classes
VEHICLE_CLASSES = {
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck"
}

PERSON_CLASS = 0


class TrafficDetector:
    def __init__(self, model_path="yolo11l.pt", conf_threshold=0.4):
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold

    def detect(self, frame):
        """
        Run object detection on frame.
        Returns structured detections.
        """

        results = self.model(frame, verbose=False)

        detections = []

        for result in results:
            boxes = result.boxes

            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())

                if conf < self.conf_threshold:
                    continue

                if cls_id not in VEHICLE_CLASSES and cls_id != PERSON_CLASS:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                label = VEHICLE_CLASSES.get(cls_id, "person")

                detections.append({
                    "bbox": [x1, y1, x2, y2],
                    "confidence": conf,
                    "class_id": cls_id,
                    "label": label
                })

        return detections
