import threading
from conveyor import ConveyorBelt
from capture import CameraCapture
from hailo_detector import HailoObjectDetector
from sorter import Sorter
import time


class SortingSystem:
    def __init__(self):
        """
        Initialize the sorting system with all components.
        """
        # Conveyor setup
        self.conveyor = ConveyorBelt(step_pin=17, dir_pin=27, max_speed=1.0)

        # Object detection setup
        self.detector = HailoObjectDetector()  # Configure the detector as per its implementation

        # Camera setup
        self.camera = CameraCapture(
            width=1280,
            height=720,
            fps=30,
            detection_callback=self.detect_and_sort
        )

        # Sorter setup
        self.sorter = Sorter(servo_pin=18, bolt_angle=90, nut_angle=0, default_angle=45)

        self.running = False
        self.detected_objects = []

    def initialize_system(self):
        """
        Initialize all components.
        """
        print("Initializing sorting system...")
        self.conveyor.set_speed(0.1)  # Set initial conveyor speed
        self.camera.initialize_camera()

    def detect_and_sort(self, frame):
        """
        Callback for detecting objects and sorting based on detections.

        :param frame: Frame captured by the camera.
        """
        detected_objects = self.detector.detect(frame)
        if detected_objects:
            print(f"Detected objects: {detected_objects}")
            self.detected_objects = detected_objects  # Store detected objects for sorting
            self.sort_objects()  # Sort objects immediately after detection

        return detected_objects

    def sort_objects(self):
        """
        Sort objects based on their type and detected objects.
        """
        for detected_object in self.detected_objects:
            print(f"Sorting object: {detected_object}")
            self.sorter.handle_detection([detected_object])

    def start_sorting(self):
        """
        Start the sorting process.
        """
        self.running = True
        print("Starting sorting system...")
        
        # Start the conveyor in a separate thread to run concurrently
        conveyor_thread = threading.Thread(target=self.conveyor.start)
        conveyor_thread.daemon = True  # Make it a daemon thread so it stops when the main program stops
        conveyor_thread.start()

        try:
            # Start camera and detection in the main thread, capturing frames continuously
            self.camera.capture_and_detect()
        except KeyboardInterrupt:
            print("Stopping sorting system...")
        finally:
            self.stop_sorting()

    def stop_sorting(self):
        """
        Stop the sorting process.
        """
        self.running = False
        self.conveyor.stop()
        self.camera.cleanup()
        self.sorter.cleanup()


if __name__ == "__main__":
    print("Sorting System - Main Program")
    print("Press Ctrl+C to stop the system.")
    print("\nOptions:")
    print("1. Run locally on Raspberry Pi")
    print("2. Prepare for headless operation (future feature)")

    user_choice = input("Enter your choice (1/2): ").strip()

    if user_choice == "1":
        # Local operation on Raspberry Pi
        system = SortingSystem()
        try:
            system.initialize_system()
            system.start_sorting()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            system.stop_sorting()
    elif user_choice == "2":
        # Placeholder for future headless operation
        print("Headless operation feature will be implemented in the future.")
        # Here, you can add network communication, e.g., WebSocket or HTTP server
        # to control the system remotely from your laptop.
    else:
        print("Invalid choice. Exiting...")

# Steps for Improving Integration
# Threading for Concurrent Operations:

# The system uses threading to handle the conveyor and camera operations concurrently. However, there is a need to ensure that the detection and sorting can happen seamlessly while the conveyor moves.
# Efficient Object Detection and Sorting:

# The object detection process (which captures frames and runs through the detector) should not block the conveyor. We need to make sure detection and sorting can be done in parallel without interrupting the movement of the conveyor.
# Thread-Safe Operations:

# Since both the camera and the conveyor are running in separate threads, they should be synchronized with care to avoid conflicts, especially when accessing shared resources like the Sorter.
# Camera and Conveyor Synchronization:

# The camera should capture frames continuously, while the conveyor should move objects at the right pace to allow detection and sorting.
# Graceful System Shutdown:

# Ensuring that the system can be stopped gracefully, even during object detection and sorting operations.

# Key Changes to Ensure Seamless Performance:
# Concurrent Conveyor and Camera Threads:

# The conveyor_thread is running in parallel with the camera. This ensures that the conveyor motor operates while the camera captures frames, without blocking either process.
# Immediate Sorting:

# After detecting objects, the detect_and_sort function immediately triggers sorting. This is done in the sort_objects function, where each detected object is passed to the Sorter to be sorted accordingly.
# Thread-Safe Design:

# The camera callback (detection_callback) stores the detected objects in a shared list (self.detected_objects). Sorting is performed after detection to ensure that the servo can act on the latest detected object.
# Graceful Shutdown:

# The stop_sorting method ensures that all components are properly cleaned up. The camera.cleanup() and sorter.cleanup() are called to stop the hardware safely.
# Testing Considerations:
# Object Detection Latency: The speed of detection may affect the conveyor's motion, so you'll need to adjust the conveyor speed if the system detects objects too slowly.
# Servo Response Time: Depending on how fast the servo can move to different angles, you might need to adjust the move_to_angle function in sorter.py to give the servo enough time to settle before the next operation begins.
# Multiple Objects: Ensure the system handles multiple objects being detected in quick succession. You may want to add a mechanism to handle simultaneous detection and sorting requests if needed.