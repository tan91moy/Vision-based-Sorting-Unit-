import threading
from queue import Queue
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
        self.detected_objects_queue = Queue()  # Queue to store detected objects for sorting

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
            for obj in detected_objects:
                self.detected_objects_queue.put(obj)  # Add each detected object to the queue

    def sort_objects(self):
        """
        Sort objects based on their type and detected objects.
        """
        while not self.detected_objects_queue.empty():
            detected_object = self.detected_objects_queue.get()  # Retrieve an object from the queue
            print(f"Sorting object: {detected_object}")
            self.sorter.handle_detection([detected_object])

    def conveyor_thread_func(self):
        """
        Start the conveyor in a separate thread.
        """
        try:
            self.conveyor.start()
        except Exception as e:
            print(f"Error in conveyor thread: {e}")
            self.stop_sorting()

    def camera_thread_func(self):
        """
        Capture frames and detect objects in a separate thread.
        """
        try:
            self.camera.capture_and_detect()
        except Exception as e:
            print(f"Error in camera thread: {e}")
            self.stop_sorting()

    def start_sorting(self):
        """
        Start the sorting process.
        """
        self.running = True
        print("Starting sorting system...")

        # Start the conveyor in a separate thread
        conveyor_thread = threading.Thread(target=self.conveyor_thread_func)
        conveyor_thread.daemon = True  # Make it a daemon thread so it stops when the main program stops
        conveyor_thread.start()

        # Start the camera capture and detection in a separate thread
        camera_thread = threading.Thread(target=self.camera_thread_func)
        camera_thread.daemon = True  # Make it a daemon thread
        camera_thread.start()

        # Main thread continuously processes detected objects for sorting
        try:
            while self.running:
                self.sort_objects()  # Check and sort objects in the queue
                time.sleep(1)  # Small delay to prevent high CPU usage
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

# Camera and Conveyor in Separate Threads:

# The camera capture (camera.capture_and_detect()) and conveyor (conveyor.start()) operations are moved to separate threads to allow parallel execution.
# These threads are set to be daemon threads, ensuring they stop when the main program ends.
# Queue for Detected Objects:

# Detected objects are added to a Queue (self.detected_objects_queue) in the detect_and_sort method.
# The sort_objects method processes objects from this queue, ensuring objects are handled in a thread-safe manner.
# Error Handling in Threads:

# Exception handling has been added to both the conveyor and camera threads to prevent the system from crashing if an error occurs in either thread.
# Efficient Sorting Loop:

# The start_sorting method uses a while self.running loop to continuously process objects from the queue in the main thread.
# A small delay (time.sleep(1)) is added to reduce CPU usage while waiting for new objects to be detected.
# Benefits:
# Concurrent Operations: The conveyor and camera operations are now handled in parallel, improving system responsiveness.
# Thread-Safe Object Sorting: The queue ensures that detected objects are processed in order, without race conditions.
# Improved Error Handling: The system is more robust with error handling in the threads.