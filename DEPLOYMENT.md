# Med-Warrant 部署指南

## 快速部署（5 分钟）

### 1. 部署前端到 Vercel

最简单的方式：

1. 访问 https://vercel.com/import
2. 选择 "Import Git Repository"
3. 输入：`https://github.com/Candice0313/med-warrant`
4. 选择 "Frontend" 目录作为 Root Directory
5. 点击 "Deploy"

**注意：** Vercel 会自动检测 Vite 项目并配置部署。

**环境变量：** 在 Vercel 项目设置中添加：
```
VITE_API_BASE_URL=https://your-railway-backend-url
```

---

### 2. 部署后端到 Railway

1. 访问 https://railway.app
2. 创建新项目，选择 "Deploy from GitHub"
3. 授权 GitHub 并选择 `Candice0313/med-warrant` 仓库
4. Railway 会自动检测 Python 项目
5. 设置环境变量：
   ```
   PORT=8000
   ```
6. 点击 "Deploy"

Railway 会自动读取 `requirements.txt` 和 `Procfile` 来启动应用。

**获取后端 URL：** 部署完成后，Railway 会生成一个 URL，格式如：
```
https://med-warrant-production.up.railway.app
```

将此 URL 更新到 Vercel 的 `VITE_API_BASE_URL` 环境变量。

---

### 3. 部署 Landing Page 到 GitHub Pages

1. 在 GitHub 仓库设置中找到 "Pages"
2. 选择 "Deploy from a branch"
3. 选择 "main" 分支，选择 "/docs" 文件夹
4. 保存

Landing page 将在以下地址可用：
```
https://candice0313.github.io/med-warrant
```

---

## 完整 URL 示例

部署完成后，你会得到三个 URL：

| 组件 | URL 示例 |
|------|---------|
| Landing Page | `https://candice0313.github.io/med-warrant` |
| Frontend (Demo) | `https://med-warrant.vercel.app` |
| Backend (API) | `https://med-warrant-production.up.railway.app` |

---

## 本地开发

### 后端

```bash
cd backend
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:5173

---

## 故障排除

### 前端无法连接后端

**症状：** 前端加载但 API 请求失败

**解决：**
1. 检查 Vercel 的 `VITE_API_BASE_URL` 环境变量是否正确
2. 确保后端 URL 以 `https://` 开头
3. 检查后端是否真的在运行（访问 `https://your-backend-url/api/cases`）

### Railway 部署失败

**症状：** "Build failed" 错误

**检查清单：**
1. `requirements.txt` 是否在根目录
2. `Procfile` 是否正确
3. Python 版本 >= 3.11

### Vercel 前端部署失败

**症状：** "Build error" in Vercel dashboard

**检查清单：**
1. Root Directory 是否设置为 `frontend`
2. `npm install && npm run build` 是否能在本地成功
3. Node.js 版本 >= 18

---

## 性能优化建议

### 后端
- Railway 免费套餐自动休眠，生产环境建议付费
- 添加 Redis 缓存提升性能
- 考虑数据库迁移（从 JSON 到 PostgreSQL）

### 前端
- Vercel 已自动配置 CDN 缓存
- 后期可添加 Analytics 监控性能

---

## 成本估算

| 服务 | 免费套餐 | 预期成本 |
|------|---------|---------|
| Vercel | ✅ 包含 | 免费 |
| Railway | 500 小时/月 | 免费（开发）|
| GitHub Pages | ✅ 包含 | 免费 |

**总成本：免费** （在免费套餐范围内）

---

## 下一步

部署完成后：

1. ✅ 在 LinkedIn/简历中添加 URL
2. ✅ 进行演示测试（所有功能都能工作吗？）
3. ✅ 如有问题，检查浏览器控制台和后端日志
4. ✅ 准备面试演讲稿

---

更新日期：2026-06-05
