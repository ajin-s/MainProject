"""
PCA9685 Servo Controller Driver for SmartEduSync Robot.
Channels:
  0: Head Pan (Yaw, -90 to +90 deg)
  1: Head Tilt (Pitch, -45 to +45 deg)
  2: Left Hand Actuator (0 to 90 deg)
  3: Right Hand Actuator (0 to 90 deg)
"""
import math
import time
from typing import Dict, Tuple
from part1_companion.hardware.bus import I2CBus

PCA9685_ADDR = 0x40
MODE1 = 0x00
PRESCALE = 0xFE
LED0_ON_L = 0x06

# MG90S Pulse range at 50 Hz (~500 - 2400 us) -> counts 102 to 491
MIN_PULSE = 102
MAX_PULSE = 491

# Joint Limits (channel -> (min_deg, max_deg, default_deg))
JOINT_LIMITS: Dict[int, Tuple[float, float, float]] = {
    0: (-90.0, 90.0, 0.0),    # Head Pan
    1: (-45.0, 45.0, 0.0),    # Head Tilt
    2: (0.0, 90.0, 0.0),      # Left Hand
    3: (0.0, 90.0, 0.0),      # Right Hand
}


class ServoController:
    def __init__(self, bus_num: int = 1, force_mock: bool = False):
        self.bus = I2CBus.get_bus(bus_num, force_mock=force_mock)
        self.current_angles: Dict[int, float] = {}
        self._init_pca9685()
        self.park_all()

    def _init_pca9685(self):
        # Reset PCA9685
        self.bus.write_byte_data(PCA9685_ADDR, MODE1, 0x00)
        # Set 50 Hz PWM frequency (prescale 0x79 = 121)
        self.bus.write_byte_data(PCA9685_ADDR, MODE1, 0x10)  # Sleep mode
        self.bus.write_byte_data(PCA9685_ADDR, PRESCALE, 0x79)
        self.bus.write_byte_data(PCA9685_ADDR, MODE1, 0x00)  # Wake mode
        time.sleep(0.005)
        self.bus.write_byte_data(PCA9685_ADDR, MODE1, 0xa1)  # Auto-increment

    def _angle_to_counts(self, channel: int, angle_deg: float) -> int:
        min_deg, max_deg, _ = JOINT_LIMITS.get(channel, (-90.0, 90.0, 0.0))
        clamped_deg = max(min_deg, min(max_deg, float(angle_deg)))
        
        # Map angle from [min_deg, max_deg] to [MIN_PULSE, MAX_PULSE]
        fraction = (clamped_deg - min_deg) / (max_deg - min_deg)
        counts = int(MIN_PULSE + fraction * (MAX_PULSE - MIN_PULSE))
        return max(MIN_PULSE, min(MAX_PULSE, counts))

    def set_pwm(self, channel: int, on: int, off: int):
        reg_base = LED0_ON_L + 4 * channel
        self.bus.write_byte_data(PCA9685_ADDR, reg_base, on & 0xFF)
        self.bus.write_byte_data(PCA9685_ADDR, reg_base + 1, (on >> 8) & 0xFF)
        self.bus.write_byte_data(PCA9685_ADDR, reg_base + 2, off & 0xFF)
        self.bus.write_byte_data(PCA9685_ADDR, reg_base + 3, (off >> 8) & 0xFF)

    def _write_angle(self, channel: int, angle_deg: float):
        min_deg, max_deg, _ = JOINT_LIMITS[channel]
        clamped_angle = max(min_deg, min(max_deg, float(angle_deg)))
        counts = self._angle_to_counts(channel, clamped_angle)
        self.set_pwm(channel, 0, counts)
        self.current_angles[channel] = clamped_angle

    def set_angle(self, channel: int, angle_deg: float, speed_deg_s: float | None = None):
        """Move a supported joint, optionally using a speed-limited benchtop-safe ramp."""
        if channel not in JOINT_LIMITS:
            raise ValueError(f"Unsupported servo channel: {channel}")
        if speed_deg_s is not None and speed_deg_s <= 0:
            raise ValueError("speed_deg_s must be positive")
        min_deg, max_deg, default_deg = JOINT_LIMITS[channel]
        target = max(min_deg, min(max_deg, float(angle_deg)))
        try:
            if speed_deg_s is None:
                self._write_angle(channel, target)
                return
            current = self.current_angles.get(channel, default_deg)
            step = max(1.0, float(speed_deg_s) * 0.02)
            direction = 1.0 if target >= current else -1.0
            while abs(target - current) > step:
                current += direction * step
                self._write_angle(channel, current)
                time.sleep(0.02)
            self._write_angle(channel, target)
        except Exception:
            self.park_all()
            raise

    def park_all(self):
        """Failsafe parking all joints to default neutral positions."""
        for channel, (_, _, default_deg) in JOINT_LIMITS.items():
            self.set_angle(channel, default_deg)


if __name__ == "__main__":
    controller = ServoController(force_mock=True)
    controller.set_angle(0, 30.0)  # Head pan 30 deg
    controller.set_angle(1, -15.0) # Head tilt -15 deg
    print("ServoController initialized and benched on MockBus successfully.")
