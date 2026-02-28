# 如何下载GitHub Actions构建产物

## 📥 下载方式

### 方式1：从Actions页面下载Artifacts（开发构建）

适用于：测试版本、开发中的构建

#### 步骤：

1. **访问GitHub仓库Actions页面**
   ```
   https://github.com/wanghaoggghappy/id_card_ocr/actions
   ```
   或者：点击仓库页面顶部的 **Actions** 选项卡

2. **选择工作流**
   - 在左侧列表中，点击 **"Build Vehicle Archive Processor (Windows)"**
   - 或者查看所有运行记录

3. **找到构建记录**
   - 🟢 绿色勾号 = 构建成功
   - 🔴 红色叉号 = 构建失败
   - 🟡 黄色圆圈 = 正在构建
   
   ![GitHub Actions List](https://docs.github.com/assets/cb-33243/images/help/repository/actions-tab.png)

4. **进入构建详情**
   - 点击任意一个成功的构建记录（绿色勾号）

5. **下载Artifacts**
   - 滚动到页面底部的 **Artifacts** 区域
   - 找到 `VehicleArchiveProcessor-Windows-buildXXX.zip`
   - 点击名称即可下载

   ![Artifacts Section](https://docs.github.com/assets/cb-60258/images/help/repository/artifact-drop-down-updated.png)

**注意事项**：
- ⏰ Artifacts保留30天后自动删除
- 📦 ZIP文件大小约500MB-1GB（包含PaddleOCR）
- 🔐 需要登录GitHub账号才能下载

---

### 方式2：从Releases页面下载（正式发布）

适用于：正式版本、稳定版本

#### 步骤：

1. **访问Releases页面**
   ```
   https://github.com/wanghaoggghappy/id_card_ocr/releases
   ```
   或者：点击仓库右侧的 **Releases** 区域

2. **选择版本**
   - 最新版本会显示 **Latest** 标签
   - 点击版本号（如 `vehicle-v1.0.0`）

3. **下载文件**
   - 在 **Assets** 区域下载：
     - `VehicleArchiveProcessor-Windows-XXX.zip` - Windows应用程序
     - `Source code (zip)` - 源代码（可选）

**优势**：
- ✅ 永久保存
- ✅ 版本化管理
- ✅ 带Release说明
- ✅ 更正式、更稳定

---

### 方式3：使用GitHub CLI下载（命令行）

适用于：自动化脚本、命令行用户

#### 安装GitHub CLI

```bash
# macOS
brew install gh

# Windows (使用 winget)
winget install --id GitHub.cli

# 或下载安装包
# https://cli.github.com/
```

#### 下载Artifacts

```bash
# 1. 登录GitHub
gh auth login

# 2. 查看最近的构建
gh run list --repo wanghaoggghappy/id_card_ocr --workflow "Build Vehicle Archive Processor (Windows)"

# 3. 下载最新成功的构建产物
gh run download --repo wanghaoggghappy/id_card_ocr

# 4. 或指定运行ID下载
gh run download 1234567890 --repo wanghaoggghappy/id_card_ocr
```

---

## 🔍 如何找到最新的成功构建

### 使用过滤器

在Actions页面：
1. 点击 **Status** 下拉菜单
2. 选择 **Success** (成功)
3. 选择 **Event** → **push** 或 **workflow_dispatch**

### 看构建编号

文件名包含构建编号，例如：
- `VehicleArchiveProcessor-Windows-build42.zip`
  - `42` 是构建编号
  - 编号越大越新

---

## 📦 下载后如何使用

### 解压文件

```bash
# Windows PowerShell
Expand-Archive -Path VehicleArchiveProcessor-Windows-buildXXX.zip -DestinationPath .

# macOS/Linux
unzip VehicleArchiveProcessor-Windows-buildXXX.zip
```

### 目录结构

```
VehicleArchiveProcessor/
├── VehicleArchiveProcessor.exe    ← 主程序
├── 启动-拖放文件.bat                ← 拖放启动脚本
├── 批量处理.bat                     ← 批量处理脚本
├── 使用说明.txt                     ← 中文使用手册
├── BUILD_INFO.txt                  ← 构建信息
├── archives/                        ← 输入文件夹
├── config.yaml                      ← 配置文件
└── _internal/                       ← 依赖库（不要删除）
```

### 运行程序

**方式1：拖放式（最简单）**
```
双击 "启动-拖放文件.bat"
```

**方式2：批量处理**
```
1. 将压缩包放入 archives 文件夹
2. 双击 "批量处理.bat"
```

**方式3：命令行**
```cmd
.\VehicleArchiveProcessor.exe archive.zip
.\VehicleArchiveProcessor.exe *.zip
.\VehicleArchiveProcessor.exe --help
```

---

## 🚨 常见问题

### Q1: 找不到Artifacts区域？

**A**: 
- 确保构建已完成（绿色勾号）
- 确保已登录GitHub
- 滚动到页面最底部
- 如果还没有，说明构建失败或正在进行中

### Q2: Artifacts过期了怎么办？

**A**: 
- 重新触发构建：进入Actions → 选择工作流 → Run workflow
- 或者等待下次代码推送自动构建
- 建议使用Releases下载正式版本

### Q3: 下载速度慢？

**A**: 
- 尝试使用代理或VPN
- 使用GitHub CLI命令行工具
- 从Releases页面下载（可能更快）

### Q4: 下载的ZIP无法打开？

**A**: 
- 检查文件是否完整下载（对比大小）
- 使用7-Zip或WinRAR解压
- 重新下载

### Q5: 为什么ZIP文件这么大（500MB+）？

**A**: 
- 包含PaddleOCR模型（约300MB）
- 包含Python运行时和所有依赖库
- 这是正常的，因为是独立可执行程序

### Q6: 可以只下载EXE文件吗？

**A**: 
不可以，必须下载完整的ZIP包，因为：
- EXE依赖 `_internal/` 目录中的库
- 需要配置文件和启动脚本
- 缺少任何文件都无法运行

---

## 🎯 快速链接

| 链接 | 用途 |
|------|------|
| [Actions页面](https://github.com/wanghaoggghappy/id_card_ocr/actions) | 查看构建状态、下载Artifacts |
| [Releases页面](https://github.com/wanghaoggghappy/id_card_ocr/releases) | 下载正式版本 |
| [最新构建](https://github.com/wanghaoggghappy/id_card_ocr/actions/workflows/build-vehicle-windows.yml) | 直接进入Windows构建工作流 |

---

## 📊 构建状态徽章

添加到README.md显示构建状态：

```markdown
![Build Status](https://github.com/wanghaoggghappy/id_card_ocr/workflows/Build%20Vehicle%20Archive%20Processor%20(Windows)/badge.svg)
```

---

## 🔔 构建通知（可选配置）

### 通过Email接收通知

在工作流添加：

```yaml
- name: Send notification
  if: always()
  uses: dawidd6/action-send-mail@v3
  with:
    server_address: smtp.gmail.com
    server_port: 587
    username: ${{ secrets.EMAIL_USERNAME }}
    password: ${{ secrets.EMAIL_PASSWORD }}
    subject: Build ${{ job.status }} - VehicleArchiveProcessor
    body: |
      构建状态: ${{ job.status }}
      下载链接: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
    to: your-email@example.com
    from: GitHub Actions
```

### 通过Slack接收通知

```yaml
- name: Slack Notification
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: '构建完成！下载地址：'
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

---

## 📝 下载日志

建议记录每次下载的版本：

| 日期 | 构建号 | 版本 | 用途 | 备注 |
|------|--------|------|------|------|
| 2026-02-28 | build42 | dev | 测试 | 修复VIN提取 |
| 2026-02-25 | v1.0.0 | 正式 | 生产 | 第一个稳定版 |

---

## 💡 最佳实践

1. **开发测试**：从Artifacts下载
2. **生产使用**：从Releases下载
3. **自动化**：使用GitHub CLI
4. **备份**：保存重要版本的ZIP文件
5. **文档**：记录每个版本的变更

---

**相关文档**：
- [GITHUB_ACTIONS_GUIDE.md](GITHUB_ACTIONS_GUIDE.md) - GitHub Actions完整指南
- [QUICKSTART_BUILD.md](QUICKSTART_BUILD.md) - 快速打包指南
- [WINDOWS_BUILD_GUIDE.md](WINDOWS_BUILD_GUIDE.md) - Windows本地打包指南
