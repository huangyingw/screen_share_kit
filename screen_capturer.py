#!/usr/local/bin/python3
import os
import paramiko
import pyautogui
import subprocess
import sys
import time
import venv
import logging

# 常量定义
VENV_NAME = "venv"
REQUIREMENTS_FILE = "requirements.txt"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PATH = os.path.join(SCRIPT_DIR, VENV_NAME)
LOG_FILE = os.path.join(SCRIPT_DIR, "screen_capturer.log")

# 设置日志
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# 常量定义
VENV_NAME = "venv"
REQUIREMENTS_FILE = "requirements.txt"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PATH = os.path.join(SCRIPT_DIR, VENV_NAME)


def create_venv_if_not_exists():
    if not os.path.exists(VENV_PATH):
        print(f"Creating virtual environment: {VENV_NAME}")
        venv.create(VENV_PATH, with_pip=True)
        return True
    return False


def is_venv():
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def update_pip_and_install_dependencies():
    pip_path = os.path.join(VENV_PATH, "bin", "pip")
    python_path = os.path.join(VENV_PATH, "bin", "python")

    # 更新 pip
    subprocess.check_call(
        [python_path, "-m", "pip", "install", "--upgrade", "pip"]
    )

    # 安装或更新所有依赖
    requirements_path = os.path.join(SCRIPT_DIR, REQUIREMENTS_FILE)
    subprocess.check_call(
        [pip_path, "install", "-r", requirements_path, "--upgrade"]
    )


def run_in_venv():
    venv_python = os.path.join(VENV_PATH, "bin", "python")
    os.execv(venv_python, [venv_python] + sys.argv)


def main():
    if not is_venv():
        print("Not in the target virtual environment.")
        venv_created = create_venv_if_not_exists()
        if venv_created:
            print(
                "New virtual environment created. Installing dependencies..."
            )
            update_pip_and_install_dependencies()
        print("Switching to the virtual environment...")
        run_in_venv()
    else:
        print("Running in the correct virtual environment.")
        take_screenshot_and_send()


def take_screenshot_and_send():
    logging.info("Attempting to take a screenshot...")
    try:
        screenshot = pyautogui.screenshot()
        local_path = os.path.join(SCRIPT_DIR, "screenshot.png")
        screenshot.save(local_path)
        logging.info(f"Screenshot taken and saved as '{local_path}'.")

        remote_host = "macmini.local"
        remote_path = "~/screenshot.png"

        if send_file_rsync(local_path, f"{remote_host}:{remote_path}"):
            logging.info("Screenshot sent successfully.")
            if update_remote_clipboard(remote_host, remote_path):
                logging.info("Remote clipboard updated successfully.")
            else:
                logging.error("Failed to update remote clipboard.")
        else:
            logging.error("Failed to send screenshot.")
    except Exception as e:
        logging.exception(f"Error taking or sending screenshot: {e}")


def send_file_rsync(local_path, remote_path):
    try:
        command = ["rsync", "-avz", "--progress", local_path, remote_path]
        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            logging.info(f"rsync output: {result.stdout}")
            return True
        else:
            logging.error(f"rsync error: {result.stderr}")
            return False
    except Exception as e:
        logging.exception(f"Error during rsync operation: {e}")
        return False


def update_remote_clipboard(remote_host, remote_path):
    try:
        # 首先获取远程主机上的 HOME 路径
        get_home_cmd = ["ssh", remote_host, "echo $HOME"]
        home_result = subprocess.run(
            get_home_cmd, capture_output=True, text=True
        )
        if home_result.returncode != 0:
            logging.error(f"Failed to get remote HOME: {home_result.stderr}")
            return False

        remote_home = home_result.stdout.strip()
        full_remote_path = f"{remote_home}/{os.path.basename(remote_path)}"

        # 使用完整的绝对路径更新剪贴板
        osascript_cmd = f"""
        osascript -e 'set the clipboard to (read (POSIX file "{full_remote_path}") as JPEG picture)'
        """
        command = ["ssh", remote_host, osascript_cmd]

        result = subprocess.run(command, capture_output=True, text=True)
        if result.returncode == 0:
            logging.info("Remote clipboard updated successfully.")
            return True
        else:
            logging.error(f"Remote clipboard update error: {result.stderr}")
            return False
    except Exception as e:
        logging.exception(f"Error updating remote clipboard: {e}")
        return False


if __name__ == "__main__":
    main()
