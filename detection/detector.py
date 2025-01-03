import cv2
import numpy as np
import hailo_platform.pyhailort as hailort
import threading
import queue

class HailoObjectDetector:
    def __init__(self, hailo_hef_path, conf_threshold=0.25, iou_threshold=0.45):
        self.hailo_hef_path = hailo_hef_path
        self.conf_threshold = conf_threshold
        self.iou_threshold = iou_threshold
        self.class_mapping = {
            "bolt": "bolt",
            "nut": "nut",
            "screw_body": "bolt",
            "screw_head": "bolt"
        }
        self._load_hailo_pipeline()

        # Threading components
        self.frame_queue = queue.Queue(maxsize=10)  # Queue for frames to process
        self.result_queue = queue.Queue()  # Queue for detection results
        self.stop_thread = False

    def _load_hailo_pipeline(self):
        try:
            print(f"Loading Hailo pipeline from {self.hailo_hef_path}...")
            self.device = hailort.Device()
            self.vstreams = hailort.configure_device(self.device, self.hailo_hef_path)
        except Exception as e:
            print(f"Error loading Hailo pipeline: {e}")
            raise

    def cleanup(self):
        """
        Releases the Hailo device and its resources.
        """
        if hasattr(self, 'device'):
            self.device.close()
            print("Hailo device released.")

    def _hailo_preprocess(self, frame):
        img = cv2.resize(frame, (640, 640))  # Resize to model input size
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = img / 255.0  # Normalize the image
        img = img.transpose(2, 0, 1).astype(np.float32)  # Change to CHW format
        return img

    def _hailo_postprocess(self, raw_outputs, frame_shape):
        height, width = frame_shape[:2]
        detections = []

        for output in raw_outputs:
            if output["confidence"] > self.conf_threshold:
                x_min, y_min, x_max, y_max = output["bbox"]
                x_min = int(x_min * width)
                y_min = int(y_min * height)
                x_max = int(x_max * width)
                y_max = int(y_max * height)
                detections.append({
                    "class_id": int(output["class_id"]),
                    "confidence": float(output["confidence"]),
                    "bbox": [x_min, y_min, x_max, y_max],
                })

        detections = self._apply_nms(detections)
        return detections

    def _apply_nms(self, detections):
        if len(detections) == 0:
            return []

        boxes = np.array([det["bbox"] for det in detections])
        scores = np.array([det["confidence"] for det in detections])

        indices = cv2.dnn.NMSBoxes(boxes.tolist(), scores.tolist(), self.conf_threshold, self.iou_threshold)

        if indices is not None and len(indices) > 0:
            return [detections[i[0]] for i in indices]
        return []

    def _map_classes(self, detections):
        for detection in detections:
            original_class = detection.get("class_id")
            detection["class"] = self.class_mapping.get(original_class, "unknown")
        return detections

    def _inference_thread(self):
        """Thread that handles inference."""
        while not self.stop_thread:
            if not self.frame_queue.empty():
                frame = self.frame_queue.get()
                input_tensor = self._hailo_preprocess(frame)

                raw_outputs = []
                with self.device:
                    for vstream in self.vstreams:
                        raw_outputs = vstream.write_and_read(input_tensor)

                detections = self._hailo_postprocess(raw_outputs, frame.shape)
                detections = self._map_classes(detections)

                self.result_queue.put(detections)  # Add results to the queue

    def start_inference(self):
        """Starts the inference thread."""
        self.stop_thread = False
        self.inference_thread = threading.Thread(target=self._inference_thread, daemon=True)
        self.inference_thread.start()

    def stop_inference(self):
        """Stops the inference thread."""
        self.stop_thread = True
        self.inference_thread.join()

    def detect_objects(self, frame):
        """Detect objects using Hailo and return detection results."""
        self.frame_queue.put(frame)  # Put the frame into the processing queue
        if not self.result_queue.empty():
            detections = self.result_queue.get()  # Get results from the result queue
            detected_classes = [detection["class"] for detection in detections]
            return detected_classes
        return []

# Example usage:
if __name__ == "__main__":
    hailo_detector = HailoObjectDetector("/path/to/your/hef/file")
    hailo_detector.start_inference()

    # Simulate continuous frame capture
    for _ in range(10):  # Assume 10 frames
        frame = np.random.rand(640, 640, 3) * 255  # Simulated random frame (replace with actual frame capture)
        detected_classes = hailo_detector.detect_objects(frame)
        print("Detected Classes:", detected_classes)

    hailo_detector.stop_inference()
    hailo_detector.cleanup()



# Single-Frame Inference:

# The detect_objects method is optimized for real-time processing by handling one frame at a time.
# This change removes any batch processing code to ensure faster, real-time inference.
# Error Handling for Missing Models:

# The user is prompted to select between .pt or .onnx models, and the relevant model is loaded accordingly.
# Mapping Classes:

# Classes like screw_body and screw_head are mapped to bolt to match your requirements.
# Tweakable Parameters:

# Confidence threshold (conf_threshold): Controls the minimum confidence required for a detection to be accepted.
# IoU threshold (iou_threshold): Adjusts how much overlap is allowed before suppressing a detection in Non-Maximum Suppression (NMS).
# Image Size (640x640): The input size for YOLOv8 is fixed for the model. However, you can change the resize parameters for faster inference (though this might impact accuracy).
# NMS for Robust Detection:

# The cv2.dnn.NMSBoxes function applies Non-Maximum Suppression (NMS) to reduce redundant detections.
# Usage:
# For real-time object detection, you can feed frames from your camera (or any image) into detect_objects.
# For inference using the PyTorch model, specify the .pt file path, and for ONNX, specify the .onnx file path.


# HailoRT Integration:

# Added methods to load the Hailo pipeline using the hailort library.
# Updated the inference process to utilize Hailo's device and virtual streams.
# Preprocessing for Hailo:

# Modified input data format to match Hailo's requirements.
# Postprocessing for Hailo:

# Adjusted to handle outputs from Hailo's inference pipeline.
# Device and Pipeline Management:

# Ensures that the Hailo device is properly configured and used for inference.
# Notes:
# Ensure the Hailo HEF file is available and correctly configured.
# Install the pyhailort library on your Raspberry Pi (pip install pyhailort).
# Update any path-specific variables to reflect your actual file locations.


# Changes Introduced:
# Queue for Frame Handling: A queue (frame_queue) is used to handle frames being processed. The inference thread consumes frames from the queue while the main thread can keep adding frames to be processed.
# Inference in a Separate Thread: The inference (preprocessing, model execution, postprocessing) is done in a separate thread (_inference_thread). This allows the system to continuously process frames while maintaining responsiveness.
# Result Queue: A result_queue is used to fetch the detection results from the inference thread asynchronously.
# Graceful Start and Stop: The start_inference() and stop_inference() methods manage the start/stop of the inference thread, allowing you to control when inference begins and ends.
# Performance Improvement:
# By using threading in this way, the system can:

# Continuously capture and send frames for processing without waiting for each frame to finish processing before moving to the next one.
# Improve real-time performance in high-speed environments.
# Keep the inference pipeline non-blocking and responsive.