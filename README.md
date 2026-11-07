# 🎯 宾果工坊 · Bingo Hub (bingo.zgqinc.gq)

> 互联网流行宾果游戏（Bingo）、性癖罐子（Bottle/Jar）及各类问卷量表的个人收集、在线打卡与存档工具。

本项目基于 **Google Material Web (`@material/web`)** 与 Material Design 3 风格设计，并参考 `eh.zgqinc.gq` 实现了高阶毛玻璃视效、自动暗黑/浅色主题、高精度网格对齐、可滑动百分比罐子液体填充、原图无损导出以及个人存档（`personal/`）展示系统。

---

## 🌟 核心特性

1. **精准结构识别与类型划分（不仅是 5×5）**：
   - 🧪 **罐子与瓶子量表（支持可滑动百分比）**：支持在原图画布或列表模式下直接上下拖拽/滑动设定液体百分比。
   - 🎯 **特殊规格宾果**：支持 3×5、4×4、5×5、5×7、10×6 等多种网络流行规格，具备智能连线判定。
   - 📋 **打分量表与长清单**：支持 21×3 清单勾选、分部位评分、百项打卡等多列长图格式。

2. **高规格毛玻璃设计（Glassmorphism）**：
   - 模糊半径 25~40dp，模态弹窗景深控制 60dp
   - 60%~75% Alpha 通道叠层
   - 表面覆盖微弱高斯噪点（2%~5%）
   - 1px 极细内描边（Inner Stroke）
   - 15%~20% 强调色三级色高光（Specular Highlight）

3. **自适应与手动切换明暗主题（Auto Dark/Light Mode）**：
   - 默认跟随系统 `prefers-color-scheme` 自动切换，支持手动切换（跟随系统 / 浅色 / 深色）。
   - 采用标准 Material 3 调色板。

4. **个人存档与展示系统（`personal/` 文件夹）**：
   - 支持 **「💾 导出个人记录」**：一键生成 `personal_records.json`。
   - 存入 `personal/` 目录后，全网访问即可通过顶栏的 **「👑 切换作者记录」** 按钮随时查阅作者的真实打卡结果与罐子百分比！
   - 支持访客 **「📂 导入记录」** 恢复自己的游玩记录。

5. **无损原图导出与自定义网站水印**：
   - 默认主页定位为 **`bingo.zgqinc.gq`**。
   - 导出打卡图时采用原图全分辨率离线渲染，并自动打上高质感水印横幅（包含网站域名、打卡寄语、BINGO 统计与日期）。

6. **轻量纯静态架构**：
   - 零后端依赖，无需 Node.js 运行时，可在任何静态托管服务或本地直接运行。
   - 预构建离线 Material Web 组件包，国内与离线环境加载极速。

---

## 📢 免责声明与版权说明 (Disclaimer & Copyright)

- **内容来源**：本项目收录的所有宾果游戏（Bingo）、性癖罐子（Bottle/Jar）及调查问卷模板图片均整理收集自互联网公开社群与聊天记录，绝大多数原作者未知。
- **使用目的**：本项目为开源个人项目，仅供个人打卡记录、趣味体验与社群交流，不包含任何商业营利行为。
- **侵权与署名处理**：如果您是某张图片的原创作者，希望添加署名信息、补充来源出处或申请下架，请随时通过个人主页或联系方式与我取得联系，我将在第一时间核实并处理：
  - 🌐 **个人主页**：[http://domain.zgqinc.gq](http://domain.zgqinc.gq)
  - ✈️ **Telegram**：[@ZGQinc](https://t.me/ZGQinc)

---

## 📁 目录规范

```
bingo/
├── images/                      # 个人收集的各类宾果与量表原图
├── personal/                    # 个人记录文件夹
│   └── personal_records.json    # 作者个人打卡结果与存档展示数据
├── data/
│   ├── categories.json          # 分类与图标配置
│   ├── games.json               # 游戏总览与索引库
│   └── cards/                   # 每款游戏的单独网格与数据配置
├── css/
│   └── style.css                # Material 3 样式、毛玻璃、噪点与动效
├── js/
│   ├── app.js                   # 核心交互逻辑与视图控制
│   ├── canvas-renderer.js       # 原图画板、液体填充、印记渲染与水印导出
│   ├── bingo-logic.js           # 连线算法与规则判定
│   ├── storage.js               # 本地持久化与 JSON 导入导出
│   └── material-web.bundle.js   # 离线 Google Material Web 组件库
├── index.html                   # 网页主入口
├── LICENSE                      # 开源许可证 (MIT)
└── README.md                    # 项目说明文档
```

---

## 📄 开源许可证 (License)

- 本项目代码部分遵循 [MIT License](LICENSE) 开源。
- 本项目收录与整理的图片、游戏模板等素材遵循 [知识共享署名-非商业性使用-相同方式共享 4.0 国际许可协议 (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/)。
