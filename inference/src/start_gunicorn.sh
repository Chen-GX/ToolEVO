#!/bin/bash

gunicorn_run=/YOUR_PATH_PYTHON/api_server/bin/gunicorn

export VLLM_USE_MODELSCOPE="False"

APP_MODULE="toolqa_api_serve:app"   # 指向您的 Flask 应用对象的导入路径
WORKERS=8              # 设置工作进程数量
BIND="0.0.0.0:5010"   # 设置 Gunicorn 监听的服务器地址和端口号
LOG_LEVEL="info"       # 日志级别（debug, info, warning, error, critical）

# 运行 Gunicorn 服务器
$gunicorn_run -w $WORKERS -b $BIND --timeout 120 --log-level=$LOG_LEVEL $APP_MODULE





