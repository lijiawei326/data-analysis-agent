#!/bin/bash

# 激活虚拟环境
source /home/work/disk1/LLM-ljw/agent/analysis-agent/.venv/bin/activate

# 启动Streamlit应用
streamlit run app.py --server.port 8502 --server.address 0.0.0.0 