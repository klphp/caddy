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

    # 配置 Docker 国内镜像源
    daemon_json = """{
        "userns-remap": "root",
        "registry-mirrors": ["http://hub-mirror.c.163.com", "https://docker.mirrors.ustc.edu.cn", "https://registry.docker-cn.com"]
}"""
    with open("/etc/docker/daemon.json", "w") as f:
        f.write(daemon_json)

    # 重启 Docker 服务
    run_command("systemctl restart docker")

    # 检查 Docker 信息
    # run_command("docker info")

# def install_docker_compose():
#     """安装 Docker Compose"""
#
#     # 获取 Docker Compose 版本
#     version = "v2.26.1"  # 请根据需要更改版本号
#
#     # 下载 Docker Compose
#     os_name = run_command("uname -s").strip()
#     arch = run_command("uname -m").strip()
#     url = f"https://github.com/docker/compose/releases/download/{version}/docker-compose-{os_name}-{arch}"
#     output_path = "/usr/local/bin/docker-compose"
#     response = requests.get(url, stream=True)
#     if response.status_code == 200:
#         with open(output_path, "wb") as f:
#             for chunk in response.iter_content(chunk_size=8192):
#                 f.write(chunk)
#     else:
#         print(f"下载 Docker Compose 失败：{response.status_code}")
#         return
#
#     # 添加执行权限
#     run_command(f"chmod +x {output_path}")
