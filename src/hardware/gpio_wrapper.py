"""
GPIO wrapper that allows for development on non-Raspberry Pi systems
while maintaining the same interface as RPi.GPIO
"""

class PWM:
    """Mock PWM class for development."""
    def __init__(self, pin, frequency):
        self.pin = pin
        self.frequency = frequency
        print(f"PWM initialized on pin {pin} at {frequency}Hz")
        
    def start(self, duty_cycle):
        print(f"PWM started with duty cycle {duty_cycle}%")
        
    def stop(self):
        print("PWM stopped")

class GPIOWrapper:
    BCM = "BCM"
    BOARD = "BOARD"
    IN = "IN"
    OUT = "OUT"
    PUD_UP = "PUD_UP"
    PUD_DOWN = "PUD_DOWN"

    @staticmethod
    def setmode(mode):
        print(f"GPIO.setmode({mode})")

    @staticmethod
    def setup(pin, mode, pull_up_down=None):
        if pull_up_down:
            print(f"GPIO.setup(pin={pin}, mode={mode}, pull_up_down={pull_up_down})")
        else:
            print(f"GPIO.setup(pin={pin}, mode={mode})")

    @staticmethod
    def input(pin):
        print(f"GPIO.input(pin={pin})")
        return True  # Mock return value

    @staticmethod
    def output(pin, value):
        print(f"GPIO.output(pin={pin}, value={value})")

    @staticmethod
    def cleanup():
        print("GPIO.cleanup()")

    @staticmethod
    def PWM(pin, frequency):
        print(f"Creating PWM instance for pin {pin}")
        return PWM(pin, frequency)

# Usage in your main code
try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = GPIOWrapper() 