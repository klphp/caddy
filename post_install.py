import subprocess
import sys
import os
import time

def run_command(command, shell=True, cwd=None):
    """
    运行 shell 命令并显示实时输出，如果失败则退出程序。
    """
    try:
        # 使用 check_call 或 run，并设置 stdout/stderr 为 None 或 sys.stdout/sys.stderr
        # 这样子进程的输出就会直接流向当前 Python 脚本的输出
        process = subprocess.run(
            command,
            shell=shell,
            check=True, # 如果返回码非零，则会抛出 CalledProcessError 异常
            cwd=cwd,
            # stdout=None, # 默认就是 None，会将输出打印到控制台
            # stderr=None, # 默认就是 None，会将错误打印到控制台
            text=True # Python 3.7+ 推荐，用于自动解码输出为字符串
        )
        print(f"命令执行成功：{command}")
        # 如果你不需要捕获输出，直接继承是最方便的
        return "" # 不返回具体输出，因为它已经打印到控制台了
    except subprocess.CalledProcessError as e:
        print(f"命令执行失败：{command}")
        print(f"错误码：{e.returncode}")
        # subprocess.run 默认会把 stderr 打印出来，所以这里不用重复打印 e.stderr
        sys.exit(1)
    except FileNotFoundError:
        print(f"错误：命令未找到或路径不正确：{command}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"执行命令时发生未知错误：{command}", file=sys.stderr)
        print(f"错误信息：{e}", file=sys.stderr)
        sys.exit(1)

def check_in_group(group):
    """检查当前用户是否在指定组"""
    try:
        output = subprocess.check_output(["groups"], universal_newlines=True)
        return group in output.split()
    except subprocess.CalledProcessError:
        return False

def check_docker_compose_file():
    """检查docker-compose文件是否存在"""
    compose_file = "/www/docker/docker-compose.yaml"
    if not os.path.exists(compose_file):
        print(f"错误：{compose_file} 不存在")
        sys.exit(1)

def main():
    print("正在执行安装后配置...")
    
    # 1. 检查必要文件
    check_docker_compose_file()

    # 2. 更新用户组
    print("正在更新用户组...")
    try:
        # 使用sg命令更新组
        run_command("sg docker -c 'echo 尝试加入docker组'")
        
        # 使用新方法验证组更新
        if check_in_group("docker"):
            print("成功加入docker组")
        else:
            print("警告：初次验证失败，尝试直接添加用户到组...")
            run_command("sudo usermod -aG docker $USER")
            
            # 添加重试机制
            for _ in range(3):
                if check_in_group("docker"):
                    print("成功加入docker组")
                    break
                time.sleep(1)
            else:
                print("错误：无法验证用户组更新，请手动执行：")
                print("sudo usermod -aG docker $USER && newgrp docker")
                sys.exit(1)
                
    except SystemExit:
        print("警告：用户组更新过程出错，使用备用方案")
        run_command("sudo usermod -aG docker $USER")
        run_command("newgrp docker || true")
    time.sleep(3)  # 等待Docker完全重启
    
    # 3. 重启docker服务
    print("正在重启docker服务...")
    run_command("sudo systemctl daemon-reload")
    run_command("sudo systemctl restart docker")
    time.sleep(3)  # 等待Docker完全重启
    
    # 4. 启动容器
    print("正在启动容器服务...")
    run_command("cd /www/docker && docker-compose up -d && docker-compose ps")
    
    print("\n安装完成,建议删除安装目录以增强安全性")

if __name__ == "__main__":
    main()