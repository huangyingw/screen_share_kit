import pyautogui
import keyboard
import time


def take_screenshot():
    screenshot = pyautogui.screenshot()
    screenshot.save("screenshot.png")
    print("Screenshot taken and saved as 'screenshot.png'.")


def listen_for_screenshot_key():
    print("Listening for 'Ctrl + Command + K' to take a screenshot...")
    # macOS 中的 Command 键通常对应于 Windows 键
    keyboard.add_hotkey("ctrl+windows+k", take_screenshot)

    # 保持脚本运行
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting screenshot listener.")


if __name__ == "__main__":
    listen_for_screenshot_key()
