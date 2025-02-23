import os
import re
import shutil
import sys
import getpass
import utils
import requests
import ubuntu
import debian
import subprocess


def run_command(command, shell=True, cwd=None):
    """运行 shell 命令并返回输出，如果失败则退出程序"""
    print('COMMAND>>>>>>>', command)
    process = subprocess.Popen(command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"命令执行失败：{command}")
        print(stderr.decode())
        sys.exit(1)  # 退出程序，返回错误码 1
    print(stdout.decode())  # 添加这一行来打印输出
    return stdout.decode()


def check_and_delete(path):
    """
    检查路径是文件还是目录，如果是目录则删除
    :param path: 目标路径
    """
    try:
        if os.path.exists(path):  # 检查路径是否存在
            if os.path.isdir(path):  # 判断是否是目录
                print(f"{path} 是一个目录，正在删除...")
                shutil.rmtree(path)  # 递归删除目录
                print(f"目录 {path} 已删除。")
            elif os.path.isfile(path):  # 判断是否是文件
                print(f"{path} 是一个文件，无需删除。")
            else:
                print(f"{path} 既不是文件也不是目录。")
        else:
            print(f"{path} 不存在。")
    except Exception as e:
        print(f"删除 {path} 时出错: {e}")


def is_docker_compose_installed():
    """
    检查 docker-compose 是否已安装
    :return: True（已安装）或 False（未安装）
    """
    try:
        # 运行 docker-compose --version 命令
        result = subprocess.run(
            ["docker-compose", "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        # 如果命令成功执行，返回 True
        return result.returncode == 0
    except FileNotFoundError:
        # 如果 docker-compose 命令不存在，返回 False
        return False


def stop_docker_compose_containers(directory):
    """
    在指定目录下停止 docker-compose 容器
    :param directory: 目标目录路径
    """
    try:
        # 切换到目标目录
        os.chdir(directory)
        print(f"已切换到目录: {directory}")

        # 运行 docker-compose down 命令
        subprocess.run(["docker-compose", "down"], check=True)
        print("容器已停止。")
    except subprocess.CalledProcessError as e:
        print(f"停止容器时出错: {e}")
    except Exception as e:
        print(f"执行命令时出错: {e}")


def get_and_confirm_ip():
    """获取用户输入的 IP 地址并确认"""

    while True:
        ip_address = input("服务器环境请填写公网ip，内网环境请填写内网ip：")

        # 去除两侧多余字符（空格、引号等）
        ip_address = ip_address.strip()

        # 提示用户确认
        confirmation = input(f"您输入的 IP 地址是：{ip_address}，是否正确？(y/n): ")

        if confirmation.lower() == 'y':
            return ip_address
        elif confirmation.lower() == 'n':
            print("请重新输入 IP 地址。")
        else:
            print("无效的输入，请重新确认。")


def replace_ip_in_caddyfile(ip, file_path="Caddyfile"):
    """
    替换 Caddyfile 中的 [ip] 为实际公网 IP
    :param ip: 公网 IP 地址
    :param file_path: Caddyfile 文件路径
    """
    try:
        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()

        # 替换 [ip] 为实际公网 IP
        new_content = content.replace("[ip]", ip)

        # 写回文件
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(new_content)

        print(f"已将 {file_path} 中的 [ip] 替换为 {ip}。")
    except Exception as e:
        print(f"替换文件内容时出错: {e}")


def docker_compose_up():
    """在 /www/docker 目录下执行 docker-compose up -d"""
    # 切换到 /www/docker 目录
    docker_compose_dir = "/www/docker"
    # 检查 docker-compose.yaml 文件是否存在
    if not os.path.exists(os.path.join(docker_compose_dir, "docker-compose.yaml")):
        print("错误：docker-compose.yaml 文件不存在。")
        return
    # 执行 docker-compose up -d 命令
    print("docker-compose 容器正在启动，由于拉取仓库取决于带宽，可能需要几分钟，请稍候......")
    run_command("docker-compose up -d", cwd=docker_compose_dir)
    print("docker-compose up -d 命令执行完成。")


def get_os_distribution():
    """
    获取 Linux 发行版信息。
    """
    if not os.path.exists('/etc/os-release'):
        return None

    with open('/etc/os-release', 'r') as f:
        lines = f.readlines()

    os_info = {}
    for line in lines:
        line = line.strip()
        if line:
            key, value = line.split('=', 1)
            # 去除value的双引号
            os_info[key] = value.strip('"')

    return os_info


def check_group_exists(group_name):
    """检查用户组是否存在"""
    try:
        run_command(f"getent group {group_name}")
        return True  # 命令成功执行，说明用户组存在
    except SystemExit:
        return False  # 命令执行失败，说明用户组不存在


def check_user_exists(username):
    """检查用户是否存在"""
    try:
        run_command(f"id -u {username}")
        return True  # 命令成功执行，说明用户存在
    except SystemExit:
        return False  # 命令执行失败，说明用户不存在


def add_user_to_docker_group():
    """将用户添加到 docker 组"""
    username = "docker"  # 要添加的用户名
    group_name = "docker"  # 要添加的用户组名

    # 检查 docker 用户组是否存在，不存在则创建
    if not check_group_exists(group_name):
        run_command("groupadd docker")
        print(f"用户组 {group_name} 已创建。")
    else:
        print(f"用户组 {group_name} 已存在，跳过创建。")

    # 检查用户是否存在，不存在则创建
    if not check_user_exists(username):
        run_command(f"useradd -m -g {group_name} {username}")  # 使用 -g 参数指定用户组
        print(f"用户 {username} 已创建。")
    else:
        print(f"用户 {username} 已存在，跳过创建。")

    # 将用户添加到 docker 组
    run_command(f"usermod -aG docker {username}")
    print(f"用户 {username} 已添加到 {group_name} 组。")


def add_www_user_and_group():
    """添加 www 用户和用户组"""
    username = "www"  # 要添加的用户名
    group_name = "www"  # 要添加的用户组名

    # 检查 www 用户组是否存在，不存在则创建
    if not check_group_exists(group_name):
        run_command("groupadd www")
        print(f"用户组 {group_name} 已创建。")
    else:
        print(f"用户组 {group_name} 已存在，跳过创建。")

    # 检查用户是否存在，不存在则创建
    if not check_user_exists(username):
        run_command(f"useradd -m -g {group_name} {username}")
        print(f"用户 {username} 已创建。")
    else:
        print(f"用户 {username} 已存在，跳过创建。")


def install_docker_compose():
    """安装 Docker Compose"""
    version = "v2.26.1"
    os_name = run_command("uname -s").strip()
    arch = run_command("uname -m").strip()
    url = f"https://github.com/docker/compose/releases/download/{version}/docker-compose-{os_name}-{arch}"
    output_path = "/usr/local/bin/docker-compose"
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        print(f"下载 Docker Compose 失败：{response.status_code}")
        sys.exit(1)  # 退出程序，返回错误码 1
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    run_command(f"chmod +x {output_path}")


def create_directories_and_set_permissions():
    """创建目录并设置权限"""

    # 获取当前用户名和用户组名
    current_user = getpass.getuser()
    current_group = current_user  # 假设用户组名与用户名相同

    # 创建 /www/docker 目录
    os.makedirs("/www/docker", exist_ok=True)

    # 创建子目录列表
    sub_directories = ["caddy_config", "caddy_data", "config", "data", "logs"]

    # 创建子目录并设置权限
    for sub_directory in sub_directories:
        path = os.path.join("/www/docker", sub_directory)
        os.makedirs(path, exist_ok=True)
        run_command(f"chown {current_user}:{current_group} {path}")

    # 在 data 目录下创建 web 目录并设置权限
    web_dir_path = os.path.join("/www/docker/data", "web")
    os.makedirs(web_dir_path, exist_ok=True)
    run_command(f"chown www:www {web_dir_path}")

    utils.copy_item("./Caddyfile", "/www/docker/caddy_config/Caddyfile", overwrite=True)
    utils.copy_item("./config", "/www/docker/config", overwrite=False)
    utils.copy_item("./index.html", "/www/docker/data/web/index.html", overwrite=True)

    # 设置 /www/docker 目录权限
    run_command(f"chown -R www:www /www/docker/data/web")

    print("目录创建和权限设置完成。")


def copy_docker_compose_and_set_permissions():
    """复制 docker-compose.yaml 并设置权限"""

    # 源文件路径
    source_file = "./docker-compose.yaml"
    # 目标文件路径
    destination_file = "/www/docker/docker-compose.yaml"
    utils.copy_item(source_file, destination_file, overwrite=True)
    # 设置文件权限
    run_command(f"chown www:www {destination_file}")

    print(f"文件 {destination_file} 权限设置完成。")


def docker_login(registry, username, password=None):
    """
    登录 Docker 私有仓库
    :param registry: 仓库地址（如 registry.cn-hangzhou.aliyuncs.com）
    :param username: 用户名
    :param password: 密码（如果未提供，则提示用户输入）
    """
    # 如果未提供密码，提示用户输入
    if password is None:
        password = getpass.getpass("请输入 Docker 仓库密码: ")

    # 构建 docker login 命令
    command = f"sudo docker login --username={username} --password-stdin {registry}"

    try:
        # 使用 subprocess 运行命令，并通过管道输入密码
        process = subprocess.Popen(
            command,
            shell=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        # 输入密码
        stdout, stderr = process.communicate(input=password + "\n")

        # 检查命令执行结果
        if process.returncode == 0:
            print("Docker 登录成功！")
            print(stdout)
        else:
            print("Docker 登录失败！")
            print(stderr)
            sys.exit(1)
    except Exception as e:
        print(f"执行命令时出错: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 获取公网 IP
    public_ip = get_and_confirm_ip()
    if public_ip:
        # 替换 Caddyfile 中的 [ip]
        replace_ip_in_caddyfile(public_ip)

        # 检查 docker-compose 是否已安装
    if is_docker_compose_installed():
        print("docker-compose 已安装。")
        # 停止 /www/docker 目录下的容器
        stop_docker_compose_containers("/www/docker")

    # 获取系统信息
    os_info = get_os_distribution()

    if os_info:
        add_user_to_docker_group()
        add_www_user_and_group()
        if os_info.get('ID') == 'ubuntu':
            print("Ubuntu  Docker脚本安装中......")
            ubuntu.install_docker()
        elif os_info.get('ID') == 'debian':
            print("Debian Docker安装中......")
            debian.install_docker()
        else:
            print(f"当前系统是 {os_info.get('ID')}")
            sys.exit(1)  # 退出程序，返回错误码 1

        install_docker_compose()
        create_directories_and_set_permissions()
        copy_docker_compose_and_set_permissions()

        username = "5735570@qq.com"
        registry = "registry.cn-hangzhou.aliyuncs.com"
        docker_login(registry, username)

        print("Docker 登录成功，继续执行后续操作...")
        docker_compose_up()

        print("请手动以下命令：")
        print("newgrp docker")
        print("sudo systemctl restart docker")
        print("出于安全考虑，全部安装完成后建议删除本程序的安装目录")
    else:
        print("无法获取系统信息")
        sys.exit(1)  # 退出程序，返回错误码 1
