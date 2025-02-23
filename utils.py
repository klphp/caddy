import os
import shutil


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
