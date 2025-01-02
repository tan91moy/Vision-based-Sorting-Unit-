import cv2
import time
import threading

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
                detected_classes = self.detection_callback(frame)
                if detected_classes:
                    print(f"Detected objects: {detected_classes}")

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


# Example usage
if __name__ == "__main__":
    def mock_detection_callback(frame):
        """
        Mock detection callback function to simulate HailoObjectDetector processing.

        :param frame: The current frame captured from the camera.
        :return: List of detected objects (mocked).
        """
        # Simulate detection processing
        time.sleep(0.1)  # Simulate inference time
        return ["object1", "object2"]  # Mock detected objects

    camera = CameraCapture(width=1280, height=720, fps=30, detection_callback=mock_detection_callback)

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

# Key Updates:
# Detection Callback Integration:

# Added a detection_callback parameter to the CameraCapture class. This callback is responsible for receiving a captured frame and returning detected object classes.
# Real-Time Detection:

# capture_and_detect() captures frames continuously and sends them to the detection_callback for processing (e.g., HailoObjectDetector).
# Error Handling:

# Added logic to retry frame capture if it fails.
# Mock Detection Callback:

# Included a mock detection function (mock_detection_callback) for testing without actual object detection integration.
# Frame Display:

# The cv2.imshow() call displays the live camera feed for debugging and visualization purposes.
# Clean Resource Management:

# Ensures proper release of camera resources with the cleanup() method and destructor.
# Integration with HailoObjectDetector:
# To integrate with HailoObjectDetector:

# Replace mock_detection_callback with a function that utilizes HailoObjectDetector to process the captured frame and return detected object classes.
# Ensure that the HailoObjectDetector is initialized and accessible in the callback function.