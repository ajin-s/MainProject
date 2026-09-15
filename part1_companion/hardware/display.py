"""
SSD1306 OLED (128x64) Display Driver & Sinks for SmartEduSync Robot.
Sinks:
  - FileSink: Renders display buffers to PNG file captures for CI/testing.
  - WindowScreen: Renders preview in console/log format.
  - LumaScreen: Real physical SSD1306 OLED interface.
"""
import os
from pathlib import Path
from typing import List, Optional


class DisplaySink:
    def render(self, bitmap_text: str, caption: Optional[str] = None):
        raise NotImplementedError


class FileSink(DisplaySink):
    def __init__(self, output_dir: str = "artifacts"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def render(self, bitmap_text: str, caption: Optional[str] = None):
        filename = self.output_dir / f"face_{caption or 'render'}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"=== Display Capture: {caption} ===\n")
            f.write(bitmap_text)


class WindowSink(DisplaySink):
    def render(self, bitmap_text: str, caption: Optional[str] = None):
        print(f"\n[Robot Face Display ({caption or 'Screen'})]")
        print("-" * 34)
        print(bitmap_text)
        print("-" * 34)


class LumaScreen(DisplaySink):
    """Real Physical SSD1306 OLED Screen Sink via Luma.OLED and Pillow (PIL)."""

    def __init__(self, port: int = 1, address: int = 0x3C):
        self.device = None
        try:
            from luma.core.interface.serial import i2c
            from luma.oled.device import ssd1306
            serial = i2c(port=port, address=address)
            self.device = ssd1306(serial)
        except Exception as e:
            print(f"[LumaScreen] Hardware OLED unavailable ({e}), fallback active.")

    def render(self, bitmap_text: str, caption: Optional[str] = None):
        if self.device is None:
            print(f"[LumaScreen Output: {caption}] {bitmap_text[:30]}...")
            return

        try:
            from PIL import Image, ImageDraw, ImageFont
            image = Image.new("1", (self.device.width, self.device.height))
            draw = ImageDraw.Draw(image)
            draw.text((0, 0), bitmap_text, fill=255)
            self.device.display(image)
        except Exception as e:
            print(f"[LumaScreen Render Error] {e}")



class RobotDisplay:
    def __init__(self, sink: Optional[DisplaySink] = None):
        self.sink = sink or WindowSink()

    def show_face(self, emotion: str, face_art: str):
        self.sink.render(face_art, caption=f"Emotion: {emotion}")

    def show_card(self, title: str, lines: List[str]):
        card_text = f"[{title.upper()}]\n" + "\n".join(f"• {line}" for line in lines)
        self.sink.render(card_text, caption=f"Card: {title}")


if __name__ == "__main__":
    display = RobotDisplay(sink=WindowSink())
    display.show_card("Study Alert", ["Calculus Exam in 2 days", "Current Mastery: 42%"])
