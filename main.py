import os
import shutil
import sys
import requests
import ubuntu
import debian
import subprocess


def run_command(command, shell=True, cwd=None):
    """运行 shell 命令并返回输出，如果失败则退出程序"""
    print(command)
    process = subprocess.Popen(command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"命令执行失败：{command}")
        print(stderr.decode())
        sys.exit(1)  # 退出程序，返回错误码 1
    print(stdout.decode())  # 添加这一行来打印输出
    return stdout.decode()


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

    # 创建 /www/docker 目录
    os.makedirs("/www/docker", exist_ok=True)

    # 创建子目录列表
    sub_directories = ["caddy_config", "caddy_data", "config", "data", "logs"]

    # 创建子目录并设置权限
    for sub_directory in sub_directories:
        path = os.path.join("/www/docker", sub_directory)
        os.makedirs(path, exist_ok=True)
        run_command(f"chown www:www {path}")

    # 在 data 目录下创建 web 目录并设置权限
    web_dir_path = os.path.join("/www/docker/data", "web")
    os.makedirs(web_dir_path, exist_ok=True)
    run_command(f"chown www:www {web_dir_path}")

    # 设置 /www/docker 目录权限
    run_command("chown -R www:www /www/docker")

    print("目录创建和权限设置完成。")


def copy_docker_compose_and_set_permissions():
    """复制 docker-compose.yaml 并设置权限"""

    # 源文件路径
    source_file = "./docker-compose.yaml"

    # 目标文件路径
    destination_file = "/www/docker/docker-compose.yaml"

    # 检查源文件是否存在
    if not os.path.exists(source_file):
        print(f"错误：源文件 {source_file} 不存在。")
        return

    # 复制文件
    try:
        shutil.copy2(source_file, destination_file)
        print(f"文件 {source_file} 复制到 {destination_file} 成功。")
    except Exception as e:
        print(f"文件复制失败：{e}")
        return

    # 设置文件权限
    run_command(f"chown www:www {destination_file}")

    print(f"文件 {destination_file} 权限设置完成。")


def docker_login(username, password, registry):
    """使用 docker login 登录"""
    try:
        process = subprocess.Popen(
            ['sudo', 'docker', 'login', '--username', username, registry],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True  # 确保 stdin/stdout/stderr 是文本模式
        )
        stdout, stderr = process.communicate(input=password + '\n')  # 添加换行符

        if process.returncode == 0:
            print("Docker 登录成功！")
            print(stdout)
        else:
            print("Docker 登录失败！")
            print(stderr)
            sys.exit(1)  # 登录失败，退出程序，返回错误码 1

    except FileNotFoundError:
        print("错误：docker 命令未找到，请确保 Docker 已安装。")
        sys.exit(1)
    except Exception as e:
        print(f"发生未知错误：{e}")
        sys.exit(1)


def docker_compose_up():
    """在 /www/docker 目录下执行 docker-compose up -d"""

    # 切换到 /www/docker 目录
    docker_compose_dir = "/www/docker"

    # 检查 docker-compose.yaml 文件是否存在
    if not os.path.exists(os.path.join(docker_compose_dir, "docker-compose.yaml")):
        print("错误：docker-compose.yaml 文件不存在。")
        return

    # 执行 docker-compose up -d 命令
    run_command("docker-compose up -d", cwd=docker_compose_dir)

    print("docker-compose up -d 命令执行完成。")


if __name__ == "__main__":
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

        username = ""
        password = ""
        registry = "registry.cn-hangzhou.aliyuncs.com"
        docker_login(username, password, registry)

        print("Docker 登录成功，继续执行后续操作...")
        docker_compose_up()

        print("请手动以下命令：")
        print("newgrp docker")
        print("sudo systemctl start docker")
    else:
        print("无法获取系统信息")
        sys.exit(1)  # 退出程序，返回错误码 1
