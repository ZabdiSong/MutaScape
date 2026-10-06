# MutaScape 上传与使用（中文）

## 本地打开

1. 解压完整 ZIP；不能在压缩包内部直接打开网页。
2. 双击最外层的 `index.html`。不要只复制这个 HTML；`css`、`js`、`data`、`vendor` 和 `assets` 都要在旁边。
3. 浏览器应支持 WebGL（Chrome / Edge / Firefox / Safari），以显示分子模型。
4. 网站界面为英文，研究核对及上传说明提供中文版本。

不需要安装 SaaS Starter、Node、Streamlit 或 Python 来查看网站。普通功能离线可用，官网外链需要网络。

## 用你已经安装的 GitHub Desktop 上传

1. 在 GitHub 建立 MutaScape 仓库，再用 GitHub Desktop 克隆到电脑。
2. 将解压后项目文件夹**里面的所有内容**复制进仓库文件夹。
3. 仓库顶层必须直接能看到 `index.html`、`README.md`、`assets`、`css`、`js`、`data`、`vendor` 等。
4. GitHub Desktop 写提交信息，例如 `Add MutaScape research explorer`；点击 Commit to main，再点击 Push origin。
5. 不要将 ZIP 本身当作网站源码上传，也不要套一层文件夹后让 `index.html` 留在里面。

## 开 GitHub Pages

仓库页面 → Settings → Pages → Deploy from a branch → main → /(root) → Save。

部署完成后使用 GitHub 实际显示的 **Visit site** 地址。下载 ZIP 不会自动产生 GitHub 地址。给招生官的网站地址应使用 Pages 的网址，源码地址使用仓库网址。我们没有在你的账户创建或发布仓库。

GitHub Free 下，用公开仓库发布 Pages 最方便。公开网站访客通常不需要登录。以仓库里实际显示的设置及部署结果为准。

## 各文件夹要不要上传？

| 文件/文件夹 | 是否上传 | 原因 |
|---|---|---|
| index.html、css、js、data、vendor | 必须 | 网站和离线分子模型需要 |
| assets | 必须 | CIF、论文、海报、照片、预览图片和图标 |
| docs、hardware | 建议全部 | 网页里的说明链接指向这些文件 |
| original-code | 建议全部 | 提供原始 Python / micro:bit 程序下载 |
| tools | 建议保留 | 让研究计算可复现；访客不需要运行 |
| README.md、source-inventory.json、.nojekyll | 建议保留 | 项目说明、原文件映射、静态部署配置 |

不包含 node_modules，也没有大型 SaaS 工程。单个文件均小于 GitHub 网页上传常见的 25 MiB 限制；完整 ZIP 不是需要上传到 Pages 的单个源码文件。

## 如何操作网站

- 左侧选 P/A/G；只有 P 有上传的突变结构，A/G 是化学讨论场景。
- Structure：切换 WT / Mutant / Compare，选择拟合区间，拖动旋转、滚轮缩放。
- DNA：查看实际 D/E/F 链；Show nearest distance 会显示最近原子对距离。
- Network：点击四个蛋白节点，显示单独模型；不表示真实 docking。
- Pressure board：改变环境输入、接触开关和模式旋钮，按 A/B；Record snapshot 记录一次教学场景，Export 导出 JSON。
- Research & files：查看原论文、海报、幻灯片、展板照片和源码。

## 硬件连接

软件展板不需要连接任何设备。可选 Web Serial 需要支持的 Chrome/Edge 环境与实际 micro:bit；建议从 Pages 的 HTTPS 地址或本地 localhost 打开。点击 Connect board 后由你选择设备，选择与烧录程序一致的 profile。**不会自动控制舵机，也不会扫描针脚**。

先阅读 `hardware/接线与兼容性_中文.md`。网站已验证模拟输入和输出命令逻辑，未验证真实接线或物理设备。

## 发布前最优先补的研究信息

S169P 的原始参考转录本/蛋白编号、版本与完整序列。目前结构文件只证明 S231P，不足以证明 S169P 与它相同。不要把网站的教学指数写成“突变风险概率”。
