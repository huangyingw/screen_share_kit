#!/usr/local/bin/python3
import paramiko
import os
import pyautogui
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
    """
    Sends a file to a remote host via SSH and updates the clipboard.
    """
    ssh = None
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(remote_host, port=remote_port)

        # 获取远程主目录并解析远程路径
        stdin, stdout, stderr = ssh.exec_command("echo $HOME")
        home_directory = stdout.read().strip().decode()
        real_remote_path = os.path.join(home_directory, remote_path.strip("~/"))

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
    take_screenshot_and_send()
