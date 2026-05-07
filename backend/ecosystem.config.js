// /home/huili_demo/backend/ecosystem.config.js
module.exports = {
  apps: [
    {
      name: "huili_fastapi",               // 进程名称
      script: "./huili_demo_venv/bin/uvicorn",        // Linux 虚拟环境下的 uvicorn 脚本路径
      args: "main:app --host 0.0.0.0 --port 8000",   // Uvicorn 运行参数
      interpreter: "none",                 // 关键！无需 node 解释器，由 script 接管
      env: {
        PYTHONIOENCODING: "utf-8",         // 防止字符画等飞书解析的报错
      },
      log_date_format: "YYYY-MM-DD HH:mm Z"
    }
  ]
};
