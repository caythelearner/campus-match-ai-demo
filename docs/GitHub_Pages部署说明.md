# GitHub Pages 部署说明

这个项目的 `demo/index.html` 是纯静态页面，依赖的图片在 `demo/assets/` 里。因此可以直接部署到 GitHub Pages，不需要服务器、不需要 Python 环境、不需要安装依赖。

本项目已经加入 GitHub Actions 配置：

```text
.github/workflows/deploy-demo.yml
```

它会把 `demo/` 文件夹发布成 GitHub Pages 网站。发布后访问地址一般是：

```text
https://你的GitHub用户名.github.io/仓库名/
```

## 1. 第一次上传

如果你还没有 GitHub 仓库：

1. 在 GitHub 新建一个仓库，例如 `campus-match-ai-demo`。
2. 在本机进入项目目录。
3. 初始化 Git 并推送。

```bash
cd /data/newanyue/CampusMatchAI/campus_match_ai
git init
git add .
git commit -m "Deploy Campus Match AI demo"
git branch -M main
git remote add origin https://github.com/你的用户名/campus-match-ai-demo.git
git push -u origin main
```

如果 GitHub 要求登录，按提示使用 GitHub 账号或 token。

## 2. 打开 GitHub Pages

进入仓库页面：

```text
Settings -> Pages
```

在 `Build and deployment` 里选择：

```text
Source: GitHub Actions
```

然后进入：

```text
Actions -> Deploy Campus Match Demo
```

等它运行成功。成功后页面上会出现部署地址。

## 3. 以后更新 demo

每次本地重新生成前端：

```bash
TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 .venv-lite/bin/python scripts/build_html_demo.py
```

然后提交并推送：

```bash
git add demo outputs data indexes images .github docs src scripts configs
git commit -m "Update demo"
git push
```

GitHub Actions 会自动重新部署。

## 4. 注意事项

1. 不要只上传 `demo/index.html`，必须带上 `demo/assets/`。
2. 当前 `demo/` 约 16M，GitHub Pages 可以承受。
3. GitHub Pages 是静态托管，不能跑 Python、Neo4j 或本地模型。
4. 当前页面展示的数据已经被写进 HTML 和静态资源里，所以小组伙伴只需要打开网页就能看。
5. 如果仓库是 public，GitHub Free 可以用 Pages；如果是 private，需要看账号套餐是否支持 private Pages。

## 5. 常见问题

### 页面打开空白

先看：

```text
Actions -> Deploy Campus Match Demo
```

确认 workflow 是绿色成功。

### 图片不显示

检查仓库里是否存在：

```text
demo/assets/
```

### 地址应该打开哪个

使用 GitHub Actions 部署后，打开仓库 Pages 给出的根地址即可：

```text
https://你的GitHub用户名.github.io/仓库名/
```

不需要再加 `/demo/index.html`，因为 workflow 已经把 `demo/` 当成网站根目录发布。
