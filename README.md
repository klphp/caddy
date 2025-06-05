# Docker LCMP 环境安装包

## 项目介绍

这是一个用于快速部署 LNMP (Linux + Caddy + MySQL + PHP) 环境的 Docker 安装包。该安装包支持 Ubuntu 和 Debian 系统，并包含以下组件：

- Caddy (Web 服务器)
- PHP 8.2
- MySQL 5.7
- Redis
- FTP 服务

## 安装前准备

1. 确保系统为 Ubuntu 或 Debian
2. 确保有足够的磁盘空间
3. 确保有 root 权限
4. 确保已安装 Python 3

## 安装步骤

1. 查看 Python 版本

```shell
python3 -V
```

2. 安装依赖

```shell
sudo apt install -y git vim python3-pip python3-venv -y
```

3. 下载脚本

```shell
git clone https://github.com/klphp/caddy.git
cd caddy

# 重要事情说5遍
# 修改 .env.example 中的帐号密码
# 修改 .env.example 中的帐号密码
# 修改 .env.example 中的帐号密码
# 修改 .env.example 中的帐号密码
# 修改 .env.example 中的帐号密码
```

4. 执行安装脚本

```shell
sudo python3 main.py
```

5. 按照提示输入必要信息

## 配置说明

### 环境变量配置

安装过程会在 `/www/docker/.env` 创建环境变量文件，您可以修改此文件来自定义配置：

```
# MySQL配置
MYSQL_ROOT_PASSWORD=mysqlpassword

# FTP配置
FTP_USER_NAME=ftpuser
FTP_USER_PASS=ftppassword
```

### Caddy 配置

Caddy 配置文件位于 `/www/docker/caddy_config/Caddyfile`，您可以根据需要修改此文件来配置网站。

### 网站目录

默认网站目录为 `/www/docker/data/web`，您可以将网站文件放置在此目录下。

## 常见问题

1. **如何重启服务？**

   ```bash
   cd /www/docker
   sudo docker-compose restart
   ```

2. **如何查看日志？**

   ```bash
   cd /www/docker
   sudo docker-compose logs -f
   ```

3. **如何更新配置？**

   修改相应的配置文件后，重启服务：

   ```bash
   cd /www/docker
   sudo docker-compose down
   sudo docker-compose up -d
   ```

## 更新日志

### 2025-06-01

- 增强安全性：使用环境变量替代硬编码密码
- 修复代码重复问题
- 改进错误处理
- 提高系统兼容性'

## 远程管理

- 本地 docker 安装 portainer 对服务器进行管理

```shell
# docker-compose portainer 中文版
# 注意本地docker-compose.yaml保存位置选一个安全的目录，以免误删
  portainer:
    image: '6053537/portainer-ce'
    container_name: portainer
    restart: always
    ports:
      - '9009:9000'
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./data/portainer_data:/data
```

- 服务器配置

```shell
# 连接远程主机 : 证书生成等细节请参考 https://github.com/YBFACC/blog/issues/43
sudo vim /usr/lib/systemd/system/docker.service
# 注意掉原ExecStart，新增如下
ExecStart=/usr/bin/dockerd -H tcp://0.0.0.0:2375 -H unix://var/run/docker.sock

# 带认证的配置（对应自己的证书路径，证书生成见下面方法）
ExecStart=/usr/bin/dockerd -H tcp://0.0.0.0:2376 -H unix://var/run/docker.sock \
--tls \
--tlscacert=/www/tls/ca.pem \
--tlscert=/www/tls/server-cert.pem \
--tlskey=/www/tls/server-key.pem

sudo systemctl daemon-reload
sudo systemctl restart docker

# 端口开放
sudo ufw allow 2376/tcp
```
