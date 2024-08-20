#!/usr/local/bin/python3
import os
import paramiko
import pyautogui
import subprocess
import sys
import time
import venv

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
    # 导入需要的模块

    print("Attempting to take a screenshot...")
    try:
        screenshot = pyautogui.screenshot()
        local_path = os.path.join(SCRIPT_DIR, "screenshot.png")
        screenshot.save(local_path)
        print(f"Screenshot taken and saved as '{local_path}'.")
        # 定义要发送到的远程机器的参数
        remote_host = "macmini.local"
        remote_port = 22  # SSH端口
        remote_path = "~/Downloads/screenshot.png"
        # 发送文件
        send_file_ssh(remote_host, remote_port, local_path, remote_path)
    except Exception as e:
        print(f"Error taking screenshot: {e}")


def send_file_ssh(remote_host, remote_port, local_path, remote_path):
    # SSH文件发送逻辑
    ssh = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host, port=remote_port)
        # 获取远程主目录并解析远程路径
        stdin, stdout, stderr = ssh.exec_command("echo $HOME")
        home_directory = stdout.read().strip().decode()
        real_remote_path = os.path.join(
            home_directory, remote_path.strip("~/")
        )
        # 使用SCP发送文件
        with paramiko.SFTPClient.from_transport(ssh.get_transport()) as scp:
            scp.put(local_path, real_remote_path)
        # 修改剪贴板
        command = f"osascript -e 'set the clipboard to (read (POSIX file \"{real_remote_path}\") as JPEG picture)'"
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()  # 阻塞直到远程执行结束
        if exit_status == 0:
            print("Remote command executed successfully.")
        else:
            print(f"Remote command failed with exit status {exit_status}")
            print("Error:", stderr.read().decode())
    except Exception as e:
        print(f"Error during SSH operation: {e}")
    finally:
        if ssh:
            ssh.close()


if __name__ == "__main__":
    main()
