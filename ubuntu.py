import subprocess
import os
import requests


def run_command(command, shell=True):
    """运行 shell 命令并返回输出"""
    process = subprocess.Popen(command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"命令执行失败：{command}")
        print(stderr.decode())
        return None
    return stdout.decode()


def install_docker():
    """安装 Docker"""

    # 更新和升级软件包
    run_command("sudo apt update -y")
    run_command("sudo apt upgrade -y")
    run_command("sudo apt full-upgrade -y")

    # 添加 Docker 库
    run_command(
        "sudo apt install -y apt-transport-https ca-certificates curl software-properties-common gnupg lsb-release")

    # 添加 Docker GPG 密钥
    run_command(
        "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg")

    # 添加 Docker APT 仓库
    arch = run_command("dpkg --print-architecture").strip()
    release = run_command("lsb_release -cs").strip()
    repo = f"deb [arch={arch} signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu {release} stable"
    run_command(f"echo '{repo}' | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null")

    # 再次更新软件包列表
    run_command("sudo apt update -y")

    # 安装 Docker
    run_command("sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin")

    # 检查 Docker 服务状态
    run_command("systemctl status docker")

    # 设置 Docker 开机启动
    run_command("sudo systemctl start docker")
    run_command("sudo systemctl enable docker")

    # 配置 Docker 国内镜像源（中科大）
    daemon_json = """{
        "userns-remap": "www",
        "registry-mirrors": ["https://docker.mirrors.ustc.edu.cn/"]
    }"""
    with open("/etc/docker/daemon.json", "w") as f:
        f.write(daemon_json)

    # 重启 Docker 服务
    run_command("sudo systemctl restart docker")

    # 检查 Docker 信息
    # run_command("sudo docker info")


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
#     run_command(f"sudo chmod +x {output_path}")
