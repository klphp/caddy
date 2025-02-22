import shutil
import subprocess
import os
import sys

import requests


def run_command(command, shell=True, cwd=None):
    """运行 shell 命令并返回输出，如果失败则退出程序"""
    process = subprocess.Popen(command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"命令执行失败：{command}")
        print(stderr.decode())
        sys.exit(1)  # 退出程序，返回错误码 1
    print(stdout.decode()) # 添加这一行来打印输出
    return stdout.decode()


def install_docker():
    """安装 Docker"""

    # 定义源文件和目标文件路径
    source_file = "daemon.json"
    destination_file = "/etc/docker/daemon.json"

    # 检查源文件是否存在
    if os.path.exists(source_file):
        try:
            # 复制文件（覆盖目标文件）
            shutil.copy(source_file, destination_file)
            print(f"文件已成功复制到 {destination_file}")
        except Exception as e:
            print(f"复制文件时出错: {e}")
    else:
        print(f"源文件 {source_file} 不存在，请检查路径。")

    # 安装 wget 和 sudo
    run_command("apt install wget -y")

    # 添加 Docker GPG 密钥
    run_command("wget -qO- https://download.docker.com/linux/debian/gpg | apt-key add -")

    # 添加 Docker APT 仓库
    release = run_command("lsb_release -cs").strip()
    repo = f"deb [arch=amd64] https://download.docker.com/linux/debian {release} stable"
    run_command(f"echo '{repo}' | tee /etc/apt/sources.list.d/docker.list")

    # 更新软件包列表
    run_command("apt-get update")

    # 安装 Docker
    run_command("apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin")

    # 检查 Docker 服务状态
    run_command("systemctl status docker")

    # 设置 Docker 开机启动
    run_command("systemctl start docker")
    run_command("systemctl enable docker")
