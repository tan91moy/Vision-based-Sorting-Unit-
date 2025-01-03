import cv2
import time
import threading
from hailo_object_detector import HailoObjectDetector  # Make sure to import your detector class

class CameraCapture:
    def __init__(self, camera_id=0, width=640, height=480, fps=30, detection_callback=None):
        """
        Initialize the camera capture settings.

        :param camera_id: Camera ID for Raspberry Pi HQ Camera (default: 0).
        :param width: Width of the video frame.
        :param height: Height of the video frame.
        :param fps: Frames per second.
        :param detection_callback: Callback function to process detected objects.
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.fps = fps
        self.cap = None
        self.detection_callback = detection_callback  # Callback for HailoObjectDetector integration
        self.capture_thread = None
        self.running = False

    def initialize_camera(self):
        """
        Initialize the camera and apply the settings.
        """
        try:
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                raise Exception("Camera not detected. Please ensure the Raspberry Pi HQ Camera is connected.")

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.cap.set(cv2.CAP_PROP_FPS, self.fps)

            print(f"Camera initialized with resolution {self.width}x{self.height} at {self.fps} FPS.")

        except Exception as e:
            print(f"Error initializing camera: {e}")
            self.cleanup()
            raise

    def capture_and_detect(self):
        """
        Start capturing frames and send them to the detection callback for processing.
        """
        if not self.cap:
            raise Exception("Camera is not initialized. Call `initialize_camera` first.")

        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_frames)
        self.capture_thread.daemon = True  # Make sure the thread stops when the main program stops
        self.capture_thread.start()

    def _capture_frames(self):
        """
        Capture frames in a separate thread and process them.
        """
        print("Press 'q' to quit.")
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                print("Failed to capture frame. Retrying...")
                continue

            # Perform object detection using the callback
            if self.detection_callback:
                self.detection_callback(frame)  # This will draw boxes on the frame

            # Display the frame (optional)
            cv2.imshow("Camera Feed", frame)

            # Quit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Add a slight delay to match the desired FPS
            time.sleep(1 / self.fps)

    def stop_capture(self):
        """
        Stop the camera capture and close any windows.
        """
        self.running = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join()  # Wait for the capture thread to finish
        self.cleanup()

    def cleanup(self):
        """
        Release the camera resource.
        """
        if self.cap:
            self.cap.release()
            self.cap = None
            print("Camera resource released.")
        cv2.destroyAllWindows()

    def __del__(self):
        """
        Destructor to ensure the camera resource is released.
        """
        self.cleanup()


# Detection callback function that uses HailoObjectDetector
def detection_callback(frame):
    """
    Detection callback function that processes each captured frame using HailoObjectDetector.

    :param frame: The current frame captured from the camera.
    :return: None (frame is modified directly with bounding boxes and class labels).
    """
    # Initialize your HailoObjectDetector (make sure the .hef path is correct)
    detector = HailoObjectDetector(hailo_hef_path='/path/to/your/model.hef')

    # Detect objects in the frame, get bounding boxes, class labels, and probabilities
    detections = detector.detect_objects(frame)

    # Process detections: list of (bounding_box, class_name, probability)
    for detection in detections:
        bbox, class_name, probability = detection['bbox'], detection['class_name'], detection['probability']
        
        # Draw bounding box
        x1, y1, x2, y2 = bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)  # Draw green bounding box

        # Display class name and probability
        label = f"{class_name}: {probability:.2f}"
        cv2.putText(frame, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # No need to return anything as the frame is modified directly


# Example usage
if __name__ == "__main__":
    camera = CameraCapture(width=1280, height=720, fps=30, detection_callback=detection_callback)

    try:
        camera.initialize_camera()
        camera.capture_and_detect()
        # Simulate running the system for 10 seconds
        time.sleep(10)
    except Exception as e:
        print(f"Error during capture: {e}")
    finally:
        camera.stop_capture()



# Camera Detection:

# The cv2.VideoCapture is used to interface with the Raspberry Pi HQ Camera.
# If the camera is not detected, an exception is raised with a clear error message.
# Error Handling:

# Any issues during initialization or frame capture are caught, logged, and handled gracefully.
# Adjustable Settings:

# Resolution (width, height) and FPS (fps) are configurable via parameters.
# Clean Resource Management:

# Ensures the camera resource is released (self.cap.release()) even if an error occurs.
# The __del__ method acts as a fallback to release resources when the object is destroyed.
# User Instructions:

# The script shows the camera feed and provides instructions to press 'q' to quit.


# The cv2.imshow() call displays the live camera feed for debugging and visualization purposes.




# Key Changes:
# Bounding Box Drawing: In the detection_callback, each detection contains a bounding box (bbox), class name (class_name), and probability (probability). The bounding box is drawn using cv2.rectangle(), and the class name along with the probability score is displayed using cv2.putText().

# Detection Results: The detections list is assumed to be in the format {'bbox': (x1, y1, x2, y2), 'class_name': 'object_name', 'probability': score}. Adjust the structure according to the actual output format from HailoObjectDetector.

# Example Detection:
# A bounding box is drawn in green around the detected object.
# The class label and its probability (formatted to two decimal places) are displayed above the bounding box.
# Things to Adjust:
# Ensure that the path to the .hef model is correctly set in the HailoObjectDetector initialization (hailo_hef_path='/path/to/your/model.hef').
# The detection output format should match what the detect_objects method of your HailoObjectDetector returns. If the structure is different, modify how bounding boxes, class names, and probabilities are accessed.