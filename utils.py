import os
import shutil


def current_file_directory():
    """
    获取当前脚本目录
    """
    return os.path.dirname(os.path.abspath(__file__))

def copy_item(source, destination, overwrite=False):
    """
    复制文件或目录
    :param source: 源文件或目录路径
    :param destination: 目标文件或目录路径
    :param overwrite: 是否覆盖已存在的目标文件或目录，默认为 False
    """
    try:
        if os.path.exists(destination) and not overwrite:
            print(f"目标 {destination} 已存在，跳过复制。")
            return

        if os.path.isfile(source):
            shutil.copy2(source, destination)
        elif os.path.isdir(source):
            if os.path.exists(destination) and overwrite:
                shutil.rmtree(destination)  # 如果目录存在且允许覆盖，则删除
            shutil.copytree(source, destination)
        print(f"{source} 复制到 {destination} 成功。")
    except Exception as e:
        print(f"{source} 复制失败：{e}")


def clear_directory(directory):
    """清空指定目录下的所有文件和文件夹"""

    # 检查目录是否存在
    if not os.path.exists(directory):
        print(f"错误：目录 {directory} 不存在。")
        return

    # 检查目录是否是目录
    if not os.path.isdir(directory):
        print(f"错误：{directory} 不是一个目录。")
        return

    try:
        # 遍历目录下的所有文件和文件夹
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)

            # 判断是文件还是文件夹
            if os.path.isfile(file_path):
                os.unlink(file_path)  # 删除文件
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)  # 删除文件夹

        print(f"目录 {directory} 已清空。")
    except Exception as e:
        print(f"清空目录 {directory} 时出错：{e}")