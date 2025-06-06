import os
import time
import json
import shutil
import sys
import getpass
import utils
import requests
import ubuntu
import debian
import subprocess

def run_command(command, shell=True, cwd=None):
    """
    运行 shell 命令，捕获并打印实时输出，如果失败则退出程序。
    返回命令的标准输出 (stdout)。
    """
    print(f"COMMAND>>>>>>> {command}") # 打印要执行的命令

    try:
        process = subprocess.run(
            command,
            shell=shell,
            check=True, # 如果返回码非零，则会抛出 CalledProcessError 异常
            cwd=cwd,
            stdout=subprocess.PIPE, # 关键：捕获标准输出
            stderr=subprocess.PIPE, # 关键：捕获标准错误
            text=True # Python 3.7+ 推荐，用于自动解码输出为字符串
        )

        # 打印标准输出到控制台 (实时效果取决于输出量，这里是完成捕获后一次性打印)
        if process.stdout:
            sys.stdout.write(process.stdout)
            sys.stdout.flush() # 强制刷新缓冲区

        # 打印标准错误到控制台
        if process.stderr:
            sys.stderr.write(process.stderr)
            sys.stderr.flush()

        print(f"命令执行成功：{command}")
        
        # 返回捕获到的标准输出
        return process.stdout.strip() # .strip() 移除首尾空白字符，包括换行符

    except subprocess.CalledProcessError as e:
        # 在异常中，e.stdout 和 e.stderr 包含了命令的输出
        # 即使命令失败，也要打印它们的输出，以便调试
        if e.stdout:
            sys.stdout.write(e.stdout)
            sys.stdout.flush()
        if e.stderr:
            sys.stderr.write(e.stderr)
            sys.stderr.flush()
            
        print(f"命令执行失败：{command}", file=sys.stderr)
        print(f"错误码：{e.returncode}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"错误：命令未找到或路径不正确：{command}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"执行命令时发生未知错误：{command}", file=sys.stderr)
        print(f"错误信息：{e}", file=sys.stderr)
        sys.exit(1)
        print(f"执行命令时发生未知错误：{command}", file=sys.stderr)
        print(f"错误信息：{e}", file=sys.stderr)
        sys.exit(1)

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

def get_www_uid_gid():
    """获取www用户的UID和GID"""
    try:
        uid = run_command("id -u www")
        gid = run_command("id -g www")
        return uid, gid
    except SystemExit:
        print("获取www用户UID/GID失败")
        return None, None

def configure_docker_userns(uid, gid):
    """配置docker的userns-remap
    格式说明: "UID:GID" (前面是用户ID，后面是组ID)
    """
    daemon_config = {
        "userns-remap": f"{uid}:{gid}"  # 格式: "用户ID:组ID"
    }
    
    # 确保/etc/docker目录存在
    run_command("mkdir -p /etc/docker")
    
    # 写入daemon.json
    config_path = "/etc/docker/daemon.json"
    with open(config_path, 'w') as f:
        json.dump(daemon_config, f, indent=2)
    
    print(f"已配置 {config_path} 使用UID:{uid} GID:{gid}")


def add_www_user_and_group():
    """添加 www 用户和用户组"""
    username = "www"  # 要添加的用户名
    group_name = "www"  # 要添加的用户组名
    target_start_id = 100000
    target_count = 65536

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

    # 检查/etc/subuid文件和/etc/subgid是否有www用户，如果没有则添加，如果有则修改，确保内容为www:100000:65536
    ensure_subuid_subgid(username, target_start_id, target_count)

def ensure_subuid_subgid(username, start_id, count):
    """
    检查并修改 /etc/subuid 和 /etc/subgid 文件，确保指定用户的映射存在且正确。
    如果文件不存在则创建。如果存在用户则修改，否则添加。
    """
    if os.geteuid() != 0:
        print("错误：此脚本需要 root 权限才能运行。请使用 sudo。", file=sys.stderr)
        sys.exit(1)

    target_line = f"{username}:{start_id}:{count}"
    
    for file_path in ["/etc/subuid", "/etc/subgid"]:
        file_name = os.path.basename(file_path)
        print(f"正在处理文件：{file_path}...")
        
        # 标志，表示是否找到并修改了指定用户的行
        user_line_found = False
        temp_lines = [] # 用于存储修改后的所有行

        if not os.path.exists(file_path):
            try:
                with open(file_path, 'w') as f:
                    f.write(f"{target_line}\n")
                print(f"  已创建 {file_path} 并添加了 {username} 的映射。")
            except IOError as e:
                print(f"  错误：无法写入 {file_path}。原因：{e}", file=sys.stderr)
            continue # 处理下一个文件

        # 文件存在时，读取所有行进行内存修改
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            for line in lines:
                if line.strip().startswith(f"{username}:"):
                    # 找到用户行，替换为目标内容
                    if line.strip() != target_line:
                        temp_lines.append(f"{target_line}\n")
                        user_line_found = True
                        print(f"  已更新 {username} 在 {file_path} 中的映射。")
                    else:
                        # 内容已经正确，无需修改
                        temp_lines.append(line)
                        user_line_found = True
                        print(f"  {username} 在 {file_path} 中的映射已是最新，无需修改。")
                else:
                    # 不是目标用户的行，保留不变
                    temp_lines.append(line)

            if not user_line_found:
                # 如果没有找到用户行，则添加新行
                temp_lines.append(f"{target_line}\n")
                user_line_found = True # 标记为已添加
                print(f"  已在 {file_path} 中为 {username} 添加新映射。")
            
            # 原子性写入：先写入临时文件，再替换原文件
            temp_file_path = f"{file_path}.tmp"
            with open(temp_file_path, 'w') as f:
                f.writelines(temp_lines)
            
            os.rename(temp_file_path, file_path) # 原子性替换
            print(f"  成功更新文件 {file_path}。")

        except IOError as e:
            print(f"  错误：处理 {file_path} 时发生IO错误。原因：{e}", file=sys.stderr)
        except Exception as e:
            print(f"  错误：处理 {file_path} 时发生未知错误。原因：{e}", file=sys.stderr)

def install_docker_compose():
    """安装 Docker Compose"""
    version = "v2.26.1"
    os_name = run_command("uname -s")
    arch = run_command("uname -m")
    url = f"https://github.com/docker/compose/releases/download/{version}/docker-compose-{os_name}-{arch}"
    # 判断是否已下载，若没已经下载跳过后续任务
    if os.path.exists("/usr/local/bin/docker-compose"):
        print(f"已下载 {url}，跳过任务...")
        return

    # 下载
    print(f"正在下载 {url}，请稍候...")
    output_path = "/usr/local/bin/docker-compose"
    response = requests.get(url, stream=True)
    if response.status_code != 200:
        print(f"下载 Docker Compose 失败：{response.status_code}")
        sys.exit(1)  # 退出程序，返回错误码 1
    with open(output_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    run_command(f"chmod +x {output_path}")


def replace_ip_in_caddyfile(ip):
    # 替换docker-compose.yaml中的localhost为公网Ip
    source_file = os.path.join(utils.current_file_directory(), 'docker-compose.yaml')
    with open(source_file, 'r') as f:
        content = f.read()
    new_content = content.replace('localhost', ip)
    with open(source_file, 'w') as f:
        f.write(new_content)

    # 替换Caddyfile中的[ip]
    source_file = os.path.join(utils.current_file_directory(), 'Caddyfile')
    directory_to_clear = "/www/docker/caddy_config/"
    utils.clear_directory(directory_to_clear)
    destination_file = os.path.join(directory_to_clear, os.path.basename(source_file))
    ip_address = ip

    # 检查源文件是否存在
    if not os.path.exists(source_file):
        print(f"错误：源文件 {source_file} 不存在。")
        sys.exit(1)  # 使用sys.exit替代exit

    try:
        # 读取源文件内容
        with open(source_file, "r") as f:
            content = f.read()

        # 替换 [ip] 为 127.0.0.1
        new_content = content.replace("[ip]", ip_address)

        # 写入目标文件
        with open(destination_file, "w") as f:
            f.write(new_content)

        print(f"已将 {source_file} 中的 [ip] 替换为 {ip_address}，并写入 {destination_file}。")
    except Exception as e:
        print(f"替换文件内容或写入文件时出错：{e}")
        sys.exit(1)  # 使用sys.exit替代exit


def create_env_file():
    """创建.env文件，用于存储环境变量"""
    source_file = os.path.join(utils.current_file_directory(), '.env.example')
    destination_file = "/www/docker/.env"
    
    # 检查源文件是否存在
    if not os.path.exists(source_file):
        print(f"警告：.env.example 文件不存在，将创建默认的 .env 文件。")
        # 创建默认的 .env 文件内容
        env_content = """# Docker LNMP环境变量配置

# MySQL配置
MYSQL_ROOT_PASSWORD=mysqlpassword

# FTP配置
FTP_USER_NAME=ftpuser
FTP_USER_PASS=ftppassword
"""
        with open(destination_file, "w") as f:
            f.write(env_content)
    else:
        # 如果目标文件已存在，询问用户是否覆盖
        if os.path.exists(destination_file):
            overwrite = input(f"{destination_file} 已存在，是否覆盖？(y/n): ")
            if overwrite.lower() != 'y':
                print(f"保留现有的 {destination_file} 文件。")
                return
        
        # 复制文件
        utils.copy_item(source_file, destination_file, overwrite=True)
    
    print(f".env 文件已创建在 {destination_file}，请根据需要修改其中的配置。")
    
    # 设置文件权限
    run_command(f"chown www:www {destination_file}")
    run_command(f"chmod 600 {destination_file}")


def create_directories_and_set_permissions():
    """创建目录并设置权限"""
    
    # 确保www用户和组存在
    add_www_user_and_group()

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
    
    # 创建MySQL配置目录
    mysql_config_dir = "/www/docker/config/mysql/etc"
    os.makedirs(mysql_config_dir, exist_ok=True)
    
    # 确保MySQL配置文件存在并且是文件而不是目录
    mysql_config_file = os.path.join(mysql_config_dir, "my.cnf")
    if os.path.isdir(mysql_config_file):
        shutil.rmtree(mysql_config_file)
    
    # 复制MySQL配置文件
    source_mysql_config = os.path.join(utils.current_file_directory(), "config/mysql/etc/my.cnf")
    if os.path.exists(source_mysql_config):
        utils.copy_item(source_mysql_config, mysql_config_file, overwrite=True)
    
    # 在 data 目录下创建 web 目录并设置权限
    web_dir_path = os.path.join("/www/docker/data", "web")
    os.makedirs(web_dir_path, exist_ok=True)
    run_command(f"chown www:www {web_dir_path}")
    
    # 创建 FTP 相关目录
    ftp_passwd_dir = os.path.join("/www/docker/data/ftp", "passwd")
    os.makedirs(ftp_passwd_dir, exist_ok=True)
    run_command(f"chown -R www:www {ftp_passwd_dir}")
    run_command(f"chmod -R 755 {ftp_passwd_dir}")

    utils.copy_item("config", "/www/docker/config", overwrite=False)
    utils.copy_item("./web/index.html", "/www/docker/data/web/index.html", overwrite=True)
    utils.copy_item("./web/phpinfo.php", "/www/docker/data/web/phpinfo.php", overwrite=True)
    utils.copy_item("./web/test.php", "/www/docker/data/web/test.php", overwrite=True)

    # 设置 /www/docker 目录权限
    run_command(f"chown -R www:www /www/docker")

    print("目录创建和权限设置完成。")


def copy_docker_compose_and_set_permissions():
    """复制 docker-compose.yaml 并设置权限"""

    # 源文件路径
    source_file = os.path.join(utils.current_file_directory(), "docker-compose.yaml")
    # 目标文件路径
    destination_file = "/www/docker/docker-compose.yaml"
    utils.copy_item(source_file, destination_file, overwrite=True)
    # 设置文件权限
    run_command(f"chown www:www {destination_file}")
    print(f"文件 {destination_file} 权限设置完成。")


def docker_login(registry, username=None, password=None):
    """
    登录 Docker 私有仓库
    :param registry: 仓库地址（如 registry.cn-hangzhou.aliyuncs.com）
    :param username: 用户名（如果未提供，则提示用户输入）
    :param password: 密码（如果未提供，则提示用户输入）
    """
    # 如果未提供用户名，提示用户输入
    if username is None:
        username = input("请输入 Docker 仓库用户名: ")
        
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
    run_command(f"apt update -y")
    public_ip = get_and_confirm_ip()
    if public_ip:
        # 检查 docker 是否已安装
        try:
            run_command("docker --version")
            print("Docker 已安装。")
        except SystemExit:
            print("Docker 未安装，将在系统检测后自动安装")
            
        # 检查 docker-compose 是否已安装
        if is_docker_compose_installed():
            print("docker-compose 已安装。")
            # 停止 /www/docker 目录下的容器
            stop_docker_compose_containers("/www/docker")

        # 创建 /www/docker 目录
        create_directories_and_set_permissions()
        # 写入 Caddyfile
        replace_ip_in_caddyfile(public_ip)
        # 创建环境变量文件
        create_env_file()

        # 获取系统信息
        os_info = get_os_distribution()

        if os_info:
         
            if os_info.get('ID') == 'ubuntu':
                print("Ubuntu  Docker脚本安装中......")
                ubuntu.install_docker()
            elif os_info.get('ID') == 'debian':
                print("Debian Docker安装中......")
                debian.install_docker()
            else:
                print(f"当前系统是 {os_info.get('ID')}")
                sys.exit(1)  # 退出程序，返回错误码 1

            add_user_to_docker_group()
            add_www_user_and_group()
            time.sleep(2)

            install_docker_compose()
            copy_docker_compose_and_set_permissions()

            registry = "registry.cn-hangzhou.aliyuncs.com"
            docker_login(registry)
            print("Docker 登录成功，继续执行后续操作...")

            print("正在执行目录权限配置...")
            run_command(f"chown -R 101000:101000 /www/docker")
            run_command(f"chmod 755 -R /www/docker")
            
            # 配置docker userns-remap
            uid, gid = get_www_uid_gid()
            if uid and gid:
                configure_docker_userns(uid, gid)
            
            print("安装完成！请运行以下命令启动服务：")
            print("sudo python3 post_install.py")
        else:
            print("无法获取系统信息")
            sys.exit(1)  # 退出程序，返回错误码 1
