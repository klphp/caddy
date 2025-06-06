import subprocess
import sys
import os
import time

def run_command(command):
    """运行命令并检查结果"""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        print(f"命令执行失败: {command}")
        print(stderr.decode())
        sys.exit(1)
    print(stdout.decode())

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