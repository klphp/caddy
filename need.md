当前项目为我使用 python 编写的 docker 环境安装包
其中包含 caddy+php+mysql+redis+nginx+ftp
其中 web 目录放了三个文件，index.html,phpinfo.php,test.php 分别用于测试 php 环境。
安装后使用 test.php 来测试目录可写权限，但目前提示 Warning: file_put_contents(./test.txt): Failed to open stream: Permission denied in /var/www/html/test.php on line 4
我猜测是因为 docker 开启了"userns-remap": "www" 原因导致的。

创建/www/docker 目录后，目前目录结构如下：
drwxr-xr-x 2 www www 4096 Jun 5 15:31 caddy_config/
drwxr-xr-x 3 100000 231072 4096 Jun 5 15:32 caddy_data/
drwxr-xr-x 3 www www 4096 Jun 5 15:25 config/
drwxr-xr-x 5 www www 4096 Jun 5 15:25 data/
-rwxr-xr-x 1 www www 2080 Jun 5 15:41 docker-compose.yaml
drwxr-xr-x 3 www www 4096 Jun 5 15:25 logs/

其中 caddy_config 用于存放 caddy 配置文件
caddy_data 用于存放 caddy 数据文件
config 用于存放 mysql 等配置文件
data 用于存放 web 数据文件
logs 用于存放日志文件

由生成出来的目录结构可以看出，其中 caddy_data 为 caddy 运行后自动生成的数据目录，其权限为 100000 231072，好像也有问题。
我猜也是由"userns-remap": "www" 导致的。但我不知道如何解决它，有什么方法能在脚本中解决这个问题吗。
