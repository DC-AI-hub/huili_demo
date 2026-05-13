# Huili Demo Deployment Guide

## 0.本地启动服务
（带有 --reload 参数可以在你修改代码后自动重启服务）
```bash
.\venv\Scripts\uvicorn.exe main:app --reload --host 0.0.0.0 --port 8000

.\venv\Scripts\pip.exe install xlrd
```
## 1. 部署环境环境准备 (Ubuntu)
本项目建议在 Ubuntu 环境下进行部署运行。
从您提供的终端记录中可以看出，您的项目根目录被放置于服务器的 `/home/huili_demo/` 中。

## 2. 后端部署 (Backend)

进入后端项目目录：
```bash
cd /home/huili_demo/backend
```

由于您的系统是 Ubuntu，并且使用了 `huili_demo_venv` 作为虚拟环境名称，请按以下步骤配置 Python 环境：

1. **创建虚拟环境：**
   ```bash
   python3 -m venv huili_demo_venv
   ```

2. **激活虚拟环境：**
   ```bash
   source huili_demo_venv/bin/activate
   ```

3. **安装依赖项：**
   利用内置的依赖文件配置库。
   ```bash
   pip3 install -r requirements.txt
   ```

4. **退出虚拟环境：**
   依赖安装完成后，可退出虚拟环境：
   ```bash
   deactivate
   ```

5. **后台运行 FastAPI 服务：**
   指定虚拟环境内的 `uvicorn` 路径，在 `0.0.0.0:8000` 端口启动服务：
   ```bash
   nohup huili_demo_venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 &
   ```

*(注：代码内的 `main.py` 已经适配了跨平台路径加载 `utils/` 下的飞书同步脚本。当检测到 Linux 系统时会自动通过 `huili_demo_venv/bin/python` 调用子脚本。)*

## 3. 前端部署 (Frontend)

1. 进入前端目录：
   ```bash
   cd /home/huili_demo/frontend
   ```
2. 安装 NPM 依赖（忽略冲突）：
   ```bash
   npm install --legacy-peer-deps
   ```
3. 编译打包：
   ```bash
   npm run build
   ```
4. *编译完成后，构建的静态资源将放在 `dist/` 文件夹内。由于在 `main.py` 内部已经配置好了对 `../frontend/dist` 的静态文件托管（StaticFiles 挂载），在 FastAPI 正常拉起的情况下就会自动托管前端页面。*

## 4. 数据库环境 (MySQL)

如果有尚未初始化的表结构，请直接导入执行：
```bash
mysql -u root -p huili < ddl.sql
```
并需确认当前服务器能够通过配置的用户名密码（默认是：`119.29.19.63` 及配置中的密码）成功连接目标数据库。
