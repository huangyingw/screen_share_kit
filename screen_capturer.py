import paramiko
import os
import pygetwindow as gw
import pyautogui
from pynput import keyboard
import time


def take_screenshot_and_send():
    """
    Captures a screenshot of the currently active window and sends it via SSH.
    """
    print("Attempting to take a screenshot...")
    try:
        screenshot = pyautogui.screenshot()
        local_path = "screenshot.png"
        screenshot.save(local_path)
        print("Screenshot taken and saved as 'screenshot.png'.")

        # 定义要发送到的远程机器的参数
        remote_host = "macmini.local"
        remote_port = 22  # SSH端口
        remote_path = "~/Downloads/screenshot.png"

        # 发送文件
        send_file_ssh(remote_host, remote_port, local_path, remote_path)
    except Exception as e:
        print(f"Error taking screenshot: {e}")


def send_file_ssh(remote_host, remote_port, local_path, remote_path):
    # SSH和SCP逻辑
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(remote_host, port=remote_port)

    # 获取远程主目录并解析远程路径
    stdin, stdout, stderr = ssh.exec_command("echo $HOME")
    home_directory = stdout.read().strip().decode()
    real_remote_path = os.path.join(home_directory, remote_path.strip("~/"))

    # 使用SCP发送文件
    scp = paramiko.SFTPClient.from_transport(ssh.get_transport())
    scp.put(local_path, real_remote_path)
    scp.close()

    # 修改剪贴板
    command = f"osascript -e 'set the clipboard to (read (POSIX file \"{real_remote_path}\") as JPEG picture)'"
    try:
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()  # 阻塞直到远程执行结束
        if exit_status == 0:
            print("Remote command executed successfully.")
        else:
            print(f"Remote command failed with exit status {exit_status}")
            print("Error:", stderr.read().decode())
    except Exception as e:
        print(f"Error executing remote command: {e}")

    ssh.close()


# 用于跟踪按键状态的集合
keys_pressed = set()


def on_press(key):
    """
    Defines the action to be taken on key press.
    """
    # 将按下的键添加到集合中
    keys_pressed.add(key)

    # 检查是否按下了指定的快捷键组合
    if (
        keyboard.Key.cmd in keys_pressed
        and keyboard.Key.ctrl in keys_pressed
        and keyboard.KeyCode.from_char("j") in keys_pressed
    ):
        take_screenshot_and_send()


def on_release(key):
    """
    Removes the key from the set when it is released.
    """
    # 将释放的键从集合中移除
    try:
        keys_pressed.remove(key)
    except KeyError:
        pass  # 忽略未被跟踪的按键


if __name__ == "__main__":
    print("Listening for 'Ctrl + Command + J' to take a screenshot...")
    # 启动监听器来监听按键
    with keyboard.Listener(
        on_press=on_press, on_release=on_release
    ) as listener:
        listener.join()
