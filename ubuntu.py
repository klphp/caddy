import subprocess
import os
import sys
import utils


def run_command(command, shell=True, cwd=None):
    """运行 shell 命令并返回输出，如果失败则退出程序"""
    process = subprocess.Popen(command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"命令执行失败：{command}")
        print(stderr.decode())
        sys.exit(1)  # 退出程序，返回错误码 1
    print(stdout.decode())  # 添加这一行来打印输出
    return stdout.decode()


def install_docker():
    """安装 Docker"""

    # 定义源文件和目标文件路径
    run_command("mkdir -p /etc/docker")
    source_file = os.path.join(utils.current_file_directory(), 'daemon.json')
    destination_file = "/etc/docker/daemon.json"

    # 检查源文件是否存在
    if os.path.exists(source_file):
        try:
            # 复制文件（覆盖目标文件）
            utils.copy_item(source_file, destination_file)
            print(f"文件已成功复制到 {destination_file}")
        except Exception as e:
            print(f"复制文件时出错: {e}")
            sys.exit(1)
    else:
        print(f"源文件 {source_file} 不存在，请检查路径。")
        sys.exit(1)

    # 更新和升级软件包
    run_command("apt update -y")
    run_command("apt upgrade -y")
    run_command("apt full-upgrade -y")

    # 添加 Docker 库
    run_command(
        "apt install -y apt-transport-https ca-certificates curl software-properties-common gnupg lsb-release")

    # 添加 Docker GPG 密钥
    run_command(
        "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg")

    # 添加 Docker APT 仓库
    arch = run_command("dpkg --print-architecture").strip()
    release = run_command("lsb_release -cs").strip()
    repo = f"deb [arch={arch} signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu {release} stable"
    run_command(f"echo '{repo}' | tee /etc/apt/sources.list.d/docker.list > /dev/null")

    # 再次更新软件包列表
    run_command("apt update -y")

    # 安装 Docker
    run_command("apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin")

    # 设置 Docker 开机启动
    run_command("systemctl start docker")
    run_command("systemctl enable docker")
    # 重启 Docker 服务
    run_command("systemctl restart docker")
