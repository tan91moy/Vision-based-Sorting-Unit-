import RPi.GPIO as GPIO
import time

class Sorter:
    def __init__(self, servo_pin=18, bolt_angle=0, nut_angle=90, default_angle=45):
        """
        Initialize sorting system with GPIO and servo control.

        :param servo_pin: GPIO pin connected to the servo motor.
        :param bolt_angle: Angle for sorting bolts.
        :param nut_angle: Angle for sorting nuts.
        :param default_angle: Default angle position.
        """
        self.servo_pin = servo_pin
        self.bolt_angle = bolt_angle
        self.nut_angle = nut_angle
        self.default_angle = default_angle

        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.servo_pin, GPIO.OUT)
        self.servo = GPIO.PWM(self.servo_pin, 50)  # 50Hz PWM frequency
        self.servo.start(0)  # Initialize with 0% duty cycle

        # Move servo to the default position
        self.move_to_angle(self.default_angle)

    def move_to_angle(self, angle):
        """
        Move the servo to a specific angle (between 0 and 180 degrees).

        :param angle: Target angle for the servo.
        """
        duty_cycle = (angle / 18) + 2  # Convert angle to duty cycle
        self.servo.ChangeDutyCycle(duty_cycle)
        print(f"Moving servo to {angle} degrees.")
        time.sleep(0.5)  # Allow the servo to reach the target position

    def sort(self, object_type):
        """
        Sort the object based on its type (either 'bolt' or 'nut').

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

        # Return to default position after sorting
        self.move_to_angle(self.default_angle)

    def handle_detection(self, detected_classes):
        """
        Handle object detection result and perform sorting.

        :param detected_classes: List of detected classes (e.g., ['bolt', 'nut']).
        """
        for detected_class in detected_classes:
            print(f"Detected: {detected_class}")
            self.sort(detected_class)

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
        # Initialize sorter with GPIO pin 18 for servo control
        sorter = Sorter(servo_pin=18)

        # Simulate integration with HailoObjectDetector
        detected_classes = ["bolt", "nut", "bolt"]  # Example detected classes
        sorter.handle_detection(detected_classes)  # Perform sorting

    except KeyboardInterrupt:
        print("Interrupted by user.")

    finally:
        sorter.cleanup()  # Clean up when done
