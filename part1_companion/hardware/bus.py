"""
I2C Bus Abstraction for SmartEduSync Robot Hardware & Mock Benchtop Testing.
"""
import os
from typing import Dict, List, Tuple


class MockBus:
    """
    Mock I2C bus recording all register writes for headless benchtop testing.
    """

    def __init__(self, bus_num: int = 1):
        self.bus_num = bus_num
        self.registers: Dict[Tuple[int, int], int] = {}
        self.write_log: List[Tuple[int, int, int]] = []

    def write_byte_data(self, addr: int, reg: int, val: int):
        self.registers[(addr, reg)] = val & 0xFF
        self.write_log.append((addr, reg, val & 0xFF))

    def read_byte_data(self, addr: int, reg: int) -> int:
        return self.registers.get((addr, reg), 0x00)

    def write_i2c_block_data(self, addr: int, reg: int, data: List[int]):
        for i, val in enumerate(data):
            self.write_byte_data(addr, reg + i, val)


class I2CBus:
    """
    Factory for real SMBus or MockBus based on HARDWARE env variable.
    """

    @staticmethod
    def get_bus(bus_num: int = 1, force_mock: bool = False):
        hw_mode = os.getenv("HARDWARE", "mock").lower()
        if force_mock or hw_mode == "mock":
            return MockBus(bus_num)

        try:
            import smbus2
            return smbus2.SMBus(bus_num)
        except Exception as e:
            print(f"[I2CBus] Warning: Real SMBus unavailable ({e}), falling back to MockBus.")
            return MockBus(bus_num)


if __name__ == "__main__":
    bus = I2CBus.get_bus(force_mock=True)
    bus.write_byte_data(0x40, 0x00, 0x10)
    print(f"MockBus write log count: {len(bus.write_log)}")
