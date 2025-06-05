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

    # 验证www用户存在
    print("验证系统用户配置...")
    run_command("id -u www")  # 如果用户不存在会抛出异常
    # 检查userns配置是否生效
    result = subprocess.run("docker info --format '{{.SecurityOptions}}'",
                          shell=True, capture_output=True, text=True)
    if "userns" not in result.stdout:
        print("错误：用户命名空间未正确配置！")
        sys.exit(1)


    # 2. 更新用户组
    print("正在更新用户组...")
    run_command("sudo newgrp docker")
    run_command("sudo usermod -aG docker www")
    
    # 2. 重启docker服务
    print("正在重启docker服务...")
    run_command("sudo systemctl daemon-reload")
    run_command("sudo systemctl restart docker")
    time.sleep(3)  # 等待Docker完全重启
        
    # 3. 验证用户组更新
    print("验证用户组配置...")
    run_command("groups www")
    
    # 4. 停止现有容器
    print("正在停止现有容器...")
    run_command("docker-compose -f /www/docker/docker-compose.yaml down")
    
    # 5. 启动容器
    print("正在启动容器服务...")
    run_command("docker-compose -f /www/docker/docker-compose.yaml up -d")
    
    print("\n安装后配置完成！")
    print("请检查服务状态：")
    print("docker-compose -f /www/docker/docker-compose.yaml ps")
    print("\n建议删除安装目录以增强安全性")

if __name__ == "__main__":
    main()