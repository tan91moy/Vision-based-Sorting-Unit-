import RPi.GPIO as GPIO
import time
from threading import Timer, Thread
from conveyor import ConveyorBelt  # Import ConveyorBelt to access speed


class Sorter:
    def __init__(self, servo_pin=18, bolt_angle=0, nut_angle=90, default_angle=45, 
                 hold_time=3, conveyor=None, distance_to_flapper=0.5):
        """
        Initialize sorting system with GPIO and servo control.

        :param servo_pin: GPIO pin connected to the servo motor.
        :param bolt_angle: Angle for sorting bolts.
        :param nut_angle: Angle for sorting nuts.
        :param default_angle: Default angle position.
        :param hold_time: Time (in seconds) to hold the servo position before returning to default.
        :param conveyor: ConveyorBelt instance for speed tracking.
        :param distance_to_flapper: Distance between the camera and sorting flapper in meters.
        """
        self.servo_pin = servo_pin
        self.bolt_angle = bolt_angle
        self.nut_angle = nut_angle
        self.default_angle = default_angle
        self.hold_time = hold_time
        self.conveyor = conveyor
        self.distance_to_flapper = distance_to_flapper

        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.servo_pin, GPIO.OUT)
        self.servo = GPIO.PWM(self.servo_pin, 50)  # 50Hz PWM frequency
        self.servo.start(0)  # Initialize with 0% duty cycle

        # Move servo to the default position
        self.move_to_angle(self.default_angle)

    def calculate_travel_time(self):
        """
        Calculate the travel time from the camera to the flapper based on conveyor speed.

        :return: Travel time in seconds.
        """
        if self.conveyor and self.conveyor.speed > 0:
            return self.distance_to_flapper / self.conveyor.speed
        else:
            raise ValueError("Conveyor speed must be greater than 0.")

    def move_to_angle(self, angle):
        """
        Move the servo to a specific angle (between 0 and 180 degrees).

        :param angle: Target angle for the servo.
        """
        duty_cycle = (angle / 18) + 2  # Convert angle to duty cycle
        self.servo.ChangeDutyCycle(duty_cycle)
        print(f"Moving servo to {angle} degrees.")
        time.sleep(0.5)  # Allow the servo to reach the target position

    def actuate_flapper(self, object_type):
        """
        Actuate the flapper based on the object type (either 'bolt' or 'nut').

        :param object_type: The detected object type ('bolt' or 'nut').
        """
        if object_type == "bolt":
            print("Sorting a bolt...")
            self.move_to_angle(self.bolt_angle)
        elif object_type == "nut":
            print("Sorting a nut...")
            self.move_to_angle(self.nut_angle)
        else:
            print("Unknown object type detected. Skipping sorting.")
            return

        # Start a timer to return servo to default position after hold time
        print(f"Hold time: {self.hold_time:.2f} seconds.")
        Timer(self.hold_time, self.move_to_angle, args=(self.default_angle,)).start()

    def handle_detection(self, detected_classes):
        """
        Handle object detection result and perform sorting.

        :param detected_classes: List of detected classes (e.g., ['bolt', 'nut']).
        """
        travel_time = self.calculate_travel_time()

        for detected_class in detected_classes:
            print(f"Detected: {detected_class}. Actuation in {travel_time:.2f} seconds.")
            Timer(travel_time, self.actuate_flapper, args=(detected_class,)).start()

    def cleanup(self):
        """
        Clean up GPIO and stop the servo.
        """
        self.move_to_angle(self.default_angle)  # Ensure servo returns to default
        self.servo.stop()
        GPIO.cleanup()


# Example usage
if __name__ == "__main__":
    try:
        # Ask user for hold time
        hold_time = float(input("Enter hold time for servo (seconds): "))

        # Initialize conveyor and sorter
        conveyor = ConveyorBelt()
        conveyor.set_speed(0.2)  # Set initial speed of the conveyor
        conveyor.start()

        sorter = Sorter(servo_pin=18, conveyor=conveyor, hold_time=hold_time)

        # Simulate integration with HailoObjectDetector
        detected_classes = ["bolt", "nut", "bolt"]  # Example detected classes
        sorter.handle_detection(detected_classes)  # Perform sorting

    except KeyboardInterrupt:
        print("Interrupted by user.")

    finally:
        sorter.cleanup()  # Clean up when done
        conveyor.cleanup()


# Integration with ConveyorBelt:

# Added a conveyor parameter to the Sorter class to access its speed dynamically.
# Dynamic Travel Time Calculation:

# The calculate_travel_time method calculates the travel time based on the conveyor's current speed and the distance to the flapper.
# Timer for Actuation:

# Uses Python's Timer to delay flapper actuation until the detected object reaches the flapper.
# Synchronization with Conveyor:

# The sorter adjusts automatically when the conveyor speed changes.
# Example Usage:

# Demonstrates initializing the conveyor and sorter and handling mock detection events.
# the hold time is now directly provided by the user through the input (hold_time = float(input("Enter hold time for servo (seconds): "))).
# The servo returns to its default position after the user-specified hold time.