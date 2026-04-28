# 🃏 记忆翻牌 - 合照头像PK游戏

> 用合照中的人头做成 4×4 记忆翻牌游戏，记录步数和时间，分享到微信群和好友PK！

## 🎮 游戏流程

1. 📸 **上传合照** — 支持任意合照
2. ✂️ **手动框选8个头像** — 在照片上拖拽方框框选
3. 🎮 **玩翻牌游戏** — 4×4 = 16张牌 = 8对头像
4. 📊 **查看成绩** — 步数 + 用时 + 评级(S/A/B/C)
5. 🔗 **生成PK链接** — 一键复制，发到微信群
6. ⚔️ **好友打开链接挑战** — 看谁步数更少！

## 🚀 5分钟部署（三选一）

### 方案A: Vercel 一键部署（推荐）

```bash
# 1. 安装 Vercel CLI
npm i -g vercel

# 2. 进入项目目录
cd memory-game

# 3. 一键部署
vercel --prod

# 完成！获得 https://memory-game-xxx.vercel.app 链接
```

**无需域名、无需备案、无需任何资质！**

### 方案B: GitHub Pages

```bash
# 1. 创建 GitHub 仓库
gh repo create memory-game --public --source=. --push

# 2. 开启 Pages
gh api repos/{owner}/memory-game/pages -X POST -f source.branch=main -f source.path=/

# 访问 https://{username}.github.io/memory-game/
```

### 方案C: ngrok 即时分享

```bash
# 本地启动
cd memory-game
python3 -m http.server 8080

# 另一个终端
ngrok http 8080
# 获得 https://xxxx.ngrok.io 链接
```

## 📱 微信分享

完成游戏后点击「生成PK链接」，复制链接发到微信群即可。

好友打开链接后会看到你的挑战成绩，上传同一张合照即可PK！

## 🏆 评级标准

| 评级 | 步数 |
|------|------|
| S 超神记忆 | ≤12步 |
| A 记忆高手 | ≤18步 |
| B 记忆不错 | ≤28步 |
| C 继续加油 | >28步 |

## 技术栈

- 纯前端，零后端依赖
- Canvas 裁剪头像
- localStorage 排行榜
- URL 参数 PK 机制
- 响应式设计，适配手机

## License

MIT
