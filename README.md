# TechTrendCrawler 新手指南

## 项目简介
TechTrendCrawler是一个专注于科技和AI领域的网络爬虫框架，用于爬取主流科技新闻网站和社交媒体平台的最新资讯与趋势。

## 开发环境准备

### 1. 安装Python
1. 访问 https://www.python.org/downloads/
2. 下载并安装最新版本的Python (建议3.8或更高版本)
3. 安装时请勾选"Add Python to PATH"选项
4. 安装完成后,打开命令提示符(cmd),输入`python --version`验证安装

### 2. 安装项目依赖
1. 打开命令提示符(cmd)
2. 进入项目目录: `cd 项目所在路径`
3. 安装依赖包: `pip install -r requirements.txt`

### 3. 安装浏览器驱动
1. 在命令提示符中运行: `python -m playwright install`
2. 这将自动安装项目所需的浏览器

## 项目结构
```
TechTrendCrawler
├── base/           # 基础类
├── config/         # 配置文件
├── news_sites/     # 新闻网站爬虫
├── trend_platforms/# 趋势平台爬虫
├── model/          # 数据模型
├── tools/          # 工具函数
└── main.py         # 程序入口
```

## 运行说明
1. 确保完成上述环境准备步骤
2. 在命令提示符中进入项目目录
3. 运行主程序: `python main.py`

## 注意事项
- 首次运行时请确保网络连接正常
- 建议使用虚拟环境进行开发
- 遇到问题请查看错误日志

## 帮助支持
如遇到问题,请参考:
1. Project.md文件中的详细说明
2. 项目目录下的示例代码
3. 相关库的官方文档 