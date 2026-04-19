import os
from typing import Optional, Tuple

import cv2
import numpy as np
import dlib


class SleepyClassifier:
    """Face-crop + YOLO classification wrapper.

    Returns (label, confidence_percent, debug_info).
    """

    def __init__(
        self,
        model_path: str = "yolo11n-sleepy-cls.pt",
        image_size: int = 224,
        device: Optional[str] = None,
    ) -> None:
        self.model_path = model_path
        self.image_size = image_size
        self.device = device
        self._model = None
        self._detector = dlib.get_frontal_face_detector()

        # Optional: dlib 68-point landmark predictor (if available)
        self._shape_predictor = None
        for candidate in (
            "shape_predictor_68_face_landmarks.dat",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "shape_predictor_68_face_landmarks.dat"),
        ):
            if os.path.exists(candidate):
                try:
                    self._shape_predictor = dlib.shape_predictor(candidate)
                except Exception:
                    self._shape_predictor = None
                break

    def get_landmarks_68_from_face_bgr(self, face_bgr: np.ndarray):
        """Returns 68 (x,y) landmarks from a face crop, or None.

        Requires `shape_predictor_68_face_landmarks.dat` to be present.
        """
        if self._shape_predictor is None:
            return None
        if face_bgr is None or face_bgr.size == 0:
            return None

        # The input is already a face crop; re-running a face detector on it can fail.
        # Instead, run the landmark predictor on the full crop rectangle.
        gray = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape[:2]
        if w < 10 or h < 10:
            return None

        rect = dlib.rectangle(left=0, top=0, right=w - 1, bottom=h - 1)
        shape = self._shape_predictor(gray, rect)
        pts = [(int(shape.part(i).x), int(shape.part(i).y)) for i in range(68)]
        return pts

    def _ensure_model(self):
        if self._model is not None:
            return

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"YOLO model not found: {self.model_path}")

        try:
            from ultralytics import YOLO
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "ultralytics is not installed. Install with: pip install ultralytics"
            ) from e

        self._model = YOLO(self.model_path)

        if self.device is not None:
            try:
                self._model.to(self.device)
            except Exception:
                pass

    def crop_first_face_bgr(self, frame_bgr: np.ndarray) -> Optional[np.ndarray]:
        """Returns a cropped face image (BGR) or None."""
        if frame_bgr is None or frame_bgr.size == 0:
            return None

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)
        rects = self._detector(gray, 1)
        if rects is None or len(rects) == 0:
            return None

        # Pick largest face by area.
        rect = max(rects, key=lambda r: r.width() * r.height())

        h_frame, w_frame = frame_bgr.shape[:2]
        x1 = max(0, rect.left())
        y1 = max(0, rect.top())
        x2 = min(w_frame, rect.right())
        y2 = min(h_frame, rect.bottom())
        if x2 <= x1 or y2 <= y1:
            return None

        # Sanity-check face area to avoid occasional "whole frame" crops.
        face_area = float((x2 - x1) * (y2 - y1))
        frame_area = float(w_frame * h_frame) if w_frame and h_frame else 0.0
        if frame_area <= 0:
            return None
        frac = face_area / frame_area
        if frac < 0.05 or frac > 0.70:
            return None

        return frame_bgr[y1:y2, x1:x2].copy()

    def predict_from_face_bgr(self, face_bgr: np.ndarray) -> Tuple[str, int, str]:
        self._ensure_model()

        # Ultralytics classify accepts numpy arrays; convert to RGB.
        face_rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)

        results = self._model.predict(face_rgb, imgsz=self.image_size, verbose=True)
        if not results:
            return "unknown", 0, "no_results"

        r0 = results[0]
        probs = getattr(r0, "probs", None)
        names = getattr(r0, "names", None) or getattr(self._model, "names", None)

        if probs is None:
            return "unknown", 0, "no_probs"

        try:
            top1 = int(probs.top1)
            top1conf = float(probs.top1conf)
        except Exception:
            # Older/newer ultralytics variations
            try:
                top1 = int(np.argmax(probs.data))
                top1conf = float(np.max(probs.data))
            except Exception:
                return "unknown", 0, "probs_parse_error"

        label = str(names.get(top1, top1) if isinstance(names, dict) else top1)
        conf_pct = int(round(100.0 * max(0.0, min(1.0, top1conf))))
        return label, conf_pct, "ok"
