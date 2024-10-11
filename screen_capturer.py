#!/usr/local/bin/python3
import os
import subprocess
import sys
import venv
import logging
from datetime import datetime

# 常量定义
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(SCRIPT_DIR, "screen_capturer.log")
VENV_NAME = "venv"
REQUIREMENTS_FILE = "requirements.txt"
VENV_PATH = os.path.join(SCRIPT_DIR, VENV_NAME)
SCREENSHOTS_DIR = os.path.join(SCRIPT_DIR, "screenshots")

# 设置日志
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


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


def get_active_window():
    from Quartz import (
        CGWindowListCopyWindowInfo,
        kCGWindowListOptionOnScreenOnly,
        kCGNullWindowID,
    )
    from Cocoa import NSWorkspace

    # 获取当前活动应用程序的 PID
    workspace = NSWorkspace.sharedWorkspace()
    active_app = workspace.frontmostApplication()
    active_pid = active_app.processIdentifier()

    # 获取所有在屏幕上的窗口
    window_list = CGWindowListCopyWindowInfo(
        kCGWindowListOptionOnScreenOnly, kCGNullWindowID
    )

    # 遍历窗口列表，找到与活动应用程序匹配的窗口
    for window in window_list:
        pid = window.get("kCGWindowOwnerPID", None)
        if pid != active_pid:
            continue
        # 检查窗口层级
        if window.get("kCGWindowLayer", 1) != 0:
            continue
        # 获取窗口 ID 和边界
        window_id = window.get("kCGWindowNumber", None)
        bounds = window.get("kCGWindowBounds", None)
        if window_id and bounds:
            return window_id, bounds
    return None, None


def take_screenshot_and_send():
    logging.info("Attempting to take a screenshot...")
    try:
        # 创建截图目录（如果不存在）
        os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

        # 生成时间戳文件名
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        filename = f"screenshot_{timestamp}.png"
        local_path = os.path.join(SCREENSHOTS_DIR, filename)

        if sys.platform == "darwin":  # macOS
            window_id, bounds = get_active_window()
            if not window_id or not bounds:
                logging.error("Failed to get active window.")
                return

            # 将窗口边界转换为 CGRect
            from Quartz import (
                CGRectMake,
                CGWindowListCreateImage,
                kCGWindowImageDefault,
                kCGWindowListOptionIncludingWindow,
                CGImageDestinationCreateWithURL,
                CGImageDestinationAddImage,
                CGImageDestinationFinalize,
            )
            from Foundation import NSURL

            x = bounds.get("X", 0)
            y = bounds.get("Y", 0)
            width = bounds.get("Width", 0)
            height = bounds.get("Height", 0)

            rect = CGRectMake(x, y, width, height)

            # 截取窗口截图
            image = CGWindowListCreateImage(
                rect,
                kCGWindowListOptionIncludingWindow,
                window_id,
                kCGWindowImageDefault,
            )

            if image:
                # 手动定义 kUTTypePNG
                kUTTypePNG = "public.png"
                # 保存截图
                url = NSURL.fileURLWithPath_(local_path)
                dest = CGImageDestinationCreateWithURL(
                    url, kUTTypePNG, 1, None
                )
                CGImageDestinationAddImage(dest, image, None)
                CGImageDestinationFinalize(dest)
                logging.info(f"Screenshot taken and saved as '{local_path}'.")
            else:
                logging.error("Failed to capture the window image.")
                return
        else:
            logging.error("This script only supports macOS.")
            return

        remote_host = "macmini.local"
        remote_screenshots_dir = "~/screenshots"

        # 修正 rsync 命令，确保只复制目录内容
        if send_file_rsync(
            f"{SCREENSHOTS_DIR}/", f"{remote_host}:{remote_screenshots_dir}/"
        ):
            logging.info("Screenshots directory sent successfully.")
            if update_remote_clipboard(
                remote_host, remote_screenshots_dir, filename
            ):
                logging.info("Remote clipboard updated successfully.")
            else:
                logging.error("Failed to update remote clipboard.")
        else:
            logging.error("Failed to send screenshots directory.")
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


def update_remote_clipboard(remote_host, remote_screenshots_dir, filename):
    try:
        # 获取远程主机上的 HOME 路径
        get_home_cmd = ["ssh", remote_host, "echo $HOME"]
        home_result = subprocess.run(
            get_home_cmd, capture_output=True, text=True
        )
        if home_result.returncode != 0:
            logging.error(f"Failed to get remote HOME: {home_result.stderr}")
            return False

        remote_home = home_result.stdout.strip()
        full_remote_dir = remote_screenshots_dir.replace("~", remote_home)
        full_remote_path = os.path.join(full_remote_dir, filename)

        # 确保路径格式正确，使用 POSIX 格式
        posix_full_remote_path = (
            full_remote_path.replace(" ", "\\ ")
            .replace("(", "\\(")
            .replace(")", "\\)")
        )

        # 使用完整的绝对路径更新剪贴板
        osascript_cmd = f"osascript -e 'set the clipboard to (read (POSIX file \"{posix_full_remote_path}\") as JPEG picture)'"
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
