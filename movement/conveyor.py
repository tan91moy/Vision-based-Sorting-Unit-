import RPi.GPIO as GPIO
import time
import threading

class ConveyorBelt:
    def __init__(self, step_pin=17, dir_pin=27, max_speed=1.0):
        """
        Initialize GPIO pins and motor control.

        :param step_pin: GPIO pin for step pulse.
        :param dir_pin: GPIO pin for direction control.
        :param max_speed: Maximum conveyor speed in m/s.
        """
        self.step_pin = step_pin
        self.dir_pin = dir_pin
        self.max_speed = max_speed
        self.running = False
        self.speed = 0.1  # Default speed in m/s
        self.pulse_interval = 1 / (self.speed * 100)  # Initial pulse interval
        self.lock = threading.Lock()  # For thread-safe speed updates
        self.direction = GPIO.HIGH  # Default direction (CLOCKWISE)

        # Set up GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.step_pin, GPIO.OUT)
        GPIO.setup(self.dir_pin, GPIO.OUT)
        GPIO.output(self.step_pin, GPIO.LOW)
        GPIO.output(self.dir_pin, self.direction)

    def set_speed(self, speed):
        """Set the speed of the conveyor belt (in m/s)."""
        with self.lock:
            if speed <= 0:
                print("Speed must be greater than 0.")
                return
            self.speed = min(speed, self.max_speed)
            self.pulse_interval = 1 / (self.speed * 100)
            print(f"Conveyor speed set to {self.speed:.2f} m/s.")

    def adjust_speed(self, step):
        """Adjust the speed in steps of 0.25 m/s."""
        new_speed = self.speed + step
        if 0 < new_speed <= self.max_speed:
            self.set_speed(new_speed)
        else:
            print("Speed adjustment out of range.")

    def start(self):
        """Start the conveyor belt by sending step pulses."""
        if not self.running:
            try:
                new_speed = float(input("Enter speed in m/s: "))
                self.set_speed(new_speed)
            except ValueError:
                print("Invalid input. Using previous speed.")
            print("Starting conveyor belt...")
            self.running = True
            threading.Thread(target=self.send_steps, daemon=True).start()
        else:
            print("Conveyor belt is already running.")

    def stop(self):
        """Stop the conveyor belt."""
        if self.running:
            print("Stopping conveyor belt...")
            self.running = False
        else:
            print("Conveyor belt is already stopped.")

    def send_steps(self):
        """Generate step pulses to control motor movement."""
        while self.running:
            GPIO.output(self.step_pin, GPIO.HIGH)
            time.sleep(0.0005)  # Pulse width
            GPIO.output(self.step_pin, GPIO.LOW)
            time.sleep(self.pulse_interval)

    def change_direction(self):
        """Toggle the direction of rotation (Clockwise / Counter-clockwise)."""
        self.direction = GPIO.LOW if self.direction == GPIO.HIGH else GPIO.HIGH
        GPIO.output(self.dir_pin, self.direction)
        print(f"Direction changed. New direction: {'CLOCKWISE' if self.direction == GPIO.HIGH else 'COUNTER-CLOCKWISE'}.")

    def cleanup(self):
        """Clean up GPIO pins."""
        self.stop()
        GPIO.cleanup()


def control_loop(conveyor):
    """Listen for user input to control the conveyor belt."""
    print("Controls: 's' - Start, 'e' - Stop, '+' - Increase Speed, '-' - Decrease Speed, 'r' - Reverse Direction, 'q' - Quit")
    while True:
        command = input("Enter command: ").strip().lower()
        if command == "s":
            conveyor.start()
        elif command == "e":
            conveyor.stop()
        elif command == "+":
            conveyor.adjust_speed(0.25)
        elif command == "-":
            conveyor.adjust_speed(-0.25)
        elif command == "r":
            conveyor.change_direction()
        elif command == "q":
            conveyor.cleanup()
            print("Exiting conveyor system.")
            break
        else:
            print("Invalid command. Try again.")


# Example usage:
if __name__ == "__main__":
    conveyor = ConveyorBelt()
    try:
        control_loop(conveyor)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        conveyor.cleanup()





# Key Features of This Code:
# GPIO-based Step and Direction Control: Uses the Raspberry Pi GPIO pins to send step pulses and control the motor’s direction.
# User Input: Allows the user to start, stop, adjust speed, and change direction of the conveyor belt.
# Speed Control: Speed can be adjusted in m/s by changing the pulse interval.
# Direction Control: Allows the user to change the direction of the conveyor.
# How It Works:
# STEP Pin: The Raspberry Pi sends a HIGH pulse to the STEP pin, which causes the motor to take a step. The interval between pulses controls the motor speed.
# DIR Pin: The DIR pin controls the direction of the motor rotation. HIGH means one direction (e.g., forward), and LOW means the opposite direction (e.g., backward).
# The program continuously sends step pulses at the calculated interval (pulse_interval) to make the motor run.
# Adjusting Speed:
# The speed is controlled by adjusting the time interval between pulses. A higher speed means a shorter interval, and a lower speed means a longer interval.
# The formula used for calculating pulse interval (self.pulse_interval = 1 / (self.speed * 100)) is just a simple example. You may need to adjust this based on your specific motor and system setup.

# Control Keys:
# s: Start the conveyor belt and ask for speed.
# e: Stop the conveyor belt.
# +: Increase speed by 0.25 m/s.
# -: Decrease speed by 0.25 m/s.
# r: Reverse or toggle the direction (Clockwise / Counter-clockwise).
# q: Quit the system and clean up resources