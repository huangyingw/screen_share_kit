import pygetwindow as gw
import pyautogui
from pynput import keyboard
import time


def take_screenshot():
    """
    Captures a screenshot of the currently active window.
    """
    print("Attempting to take a screenshot...")
    try:
        screenshot = pyautogui.screenshot()
        screenshot.save("screenshot.png")
        print("Screenshot taken and saved as 'screenshot.png'.")
    except Exception as e:
        print(f"Error taking screenshot: {e}")


def on_press(key):
    """
    Defines the action to be taken on key press.
    """
    try:
        # 定义快捷键：Ctrl + Command + J
        if (
            key == keyboard.Key.cmd
            and keyboard.Key.ctrl
            and keyboard.KeyCode.from_char("j")
        ):
            take_screenshot()
    except AttributeError:
        pass  # 忽略非目标快捷键的按键


def listen_for_screenshot_key():
    """
    Listens for a specific key combination to take a screenshot.
    """
    print("Listening for 'Ctrl + Command + J' to take a screenshot...")

    # 使用Listener来监听按键
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


if __name__ == "__main__":
    listen_for_screenshot_key()
