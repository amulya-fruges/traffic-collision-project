import json
import cv2
import torch

from PIL import Image

from transformers import (
    AutoProcessor,
    AutoModelForImageTextToText,
    BitsAndBytesConfig
)


class CosmosReasoner:

    def __init__(self):

        model_name = (
            "nvidia/Cosmos-Reason2-2B"
        )

        print("\nLoading Cosmos Reason2...\n")

        quant_config = (
            BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16
            )
        )

        self.processor = (
            AutoProcessor.from_pretrained(
                model_name,
                trust_remote_code=True
            )
        )

        self.model = (
            AutoModelForImageTextToText.from_pretrained(
                model_name,
                trust_remote_code=True,
                device_map="auto",
                quantization_config=quant_config,
                torch_dtype=torch.float16
            )
        )

        self.model.eval()

        print("\nCosmos Ready.\n")

    def extract_frames(
        self,
        clip_path,
        max_frames=4
    ):

        cap = cv2.VideoCapture(
            clip_path
        )

        total_frames = int(
            cap.get(
                cv2.CAP_PROP_FRAME_COUNT
            )
        )

        if total_frames <= 0:
            return []

        step = max(
            1,
            total_frames // max_frames
        )

        frames = []

        idx = 0

        while True:

            ret, frame = cap.read()

            if not ret:
                break

            if idx % step == 0:

                frame_rgb = (
                    cv2.cvtColor(
                        frame,
                        cv2.COLOR_BGR2RGB
                    )
                )

                image = Image.fromarray(
                    frame_rgb
                )

                frames.append(image)

                if len(frames) >= max_frames:
                    break

            idx += 1

        cap.release()

        return frames

    def build_prompt(
        self,
        event
    ):

        return f"""
You are an advanced traffic collision reasoning AI.

Analyze the temporal traffic scene carefully.

Determine:
1. Did a REAL collision occur?
2. Was there physical impact?
3. Was this merely dense traffic?
4. Was there rebound behavior?
5. Was there post-impact pause?
6. Was there dangerous driving?

Reject false positives caused by:
- side-by-side traffic
- perspective overlap
- lane compression
- near misses
- temporary occlusion

Kinematic Metadata:
{json.dumps(event, indent=2)}

Return STRICT JSON ONLY:

{{
    "collision": true/false,
    "confidence": 0.0-1.0,
    "reason": "...",
    "scene_summary": "...",
    "collision_type": "...",
    "fault_estimation": "...",
    "evidence": [
        "...",
        "..."
    ]
}}
"""

    def parse_response(
        self,
        text
    ):

        try:

            start = text.find("{")

            end = (
                text.rfind("}") + 1
            )

            parsed = json.loads(
                text[start:end]
            )

            return parsed

        except Exception as exc:

            return {
                "collision": False,
                "confidence": 0,
                "reason": str(exc)
            }

    def verify(
        self,
        clip_path,
        event
    ):

        try:

            frames = self.extract_frames(
                clip_path
            )

            if not frames:

                return {
                    "collision": False,
                    "confidence": 0,
                    "reason": "No frames extracted"
                }

            prompt = self.build_prompt(
                event
            )

            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "image": image
                        }
                        for image in frames
                    ] + [
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]

            text = (
                self.processor.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True
                )
            )

            inputs = self.processor(
                text=[text],
                images=frames,
                return_tensors="pt"
            ).to(self.model.device)

            with torch.no_grad():

                generated_ids = (
                    self.model.generate(
                        **inputs,
                        max_new_tokens=128,
                        do_sample=False
                    )
                )

            output_text = (
                self.processor.batch_decode(
                    generated_ids,
                    skip_special_tokens=True
                )[0]
            )

            return self.parse_response(
                output_text
            )

        except Exception as exc:

            return {
                "collision": False,
                "confidence": 0,
                "reason": str(exc)
            }