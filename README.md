# 生物化学学习 Skill · “101 计划”核心教材

配合“101 计划”核心教材·生物科学领域《生物化学》上下册，昌增益、施一公、王新泉主编（高等教育出版社，2025 年 12 月第 1 版），帮助检索书页、理解概念、比较代谢通路、安排复习及自测纠错。

全书共 27 章，上册 PDF 654 页，下册 PDF 587 页。技能保存学习流程、章节导航及读取工具，按需读取正文。文件有文字层，部分文字与公式识别不准确，关键内容应查看原图。

## 获取 PDF

若 Release 暂不可下载，表示该版本尚未发布；已有本地教材时仍可使用阅读、检索和渲染功能。

教材采用 [v1.0.0 Release](https://github.com/W-sir0/study-biochemistry/releases/tag/v1.0.0) 的 9 个压缩分卷（每卷最多 64 MiB）分发，文件名为 `101.zip.001` 至 `101.zip.009`。GitHub 会清理部分附件文件名，因此用压缩包保留两册 PDF 的原始中文名称、作者姓名、空格和内容。

在技能目录运行以下命令，脚本会下载各卷、逐卷核验 SHA-256、合并压缩包，再恢复原名 PDF 到 `books/`：

```bash
python3 scripts/book.py fetch --volume all
```

中断后可重试，已经下载且校验通过的分卷会复用。分卷缓存保留在 `.cache/`，两册恢复成功后可自行删除缓存以释放空间。

也可手动下载全部 9 卷，按序拼接为 `101.zip` 后解压。包内文件名为：

- `生物化学(上册) (昌增益, 施一公, 王新泉) .pdf`
- `生物化学(下册) (昌增益, 施一公, 王新泉) .pdf`

PDF 校验信息见 [books.json](references/books.json)，分卷及完整压缩包校验信息见 [archive.json](references/archive.json)。已有本地教材时可使用 `--pdf "/你的路径/教材.pdf"`，无需下载。

## 安装与使用

把整个仓库文件夹以 `study-biochemistry` 名称放到 Codex 的技能目录（默认 `~/.codex/skills/`，自定义环境使用 `$CODEX_HOME/skills/`）。例如在该目录克隆：

```bash
git clone https://github.com/W-sir0/study-biochemistry.git
```

重新加载技能列表或开启新对话后，可输入：

> 使用 $study-biochemistry 解释竞争性抑制，并用教材页码支持讲解。
>
> 使用 $study-biochemistry 比较糖酵解与糖异生，说明区室、能量与调控。
>
> 使用 $study-biochemistry 帮我安排两周复习，并先出 5 道原创自测题。

## 本地阅读工具

要求 Python 3.9+ 和 Poppler。macOS 可用 `brew install poppler`；Ubuntu/Debian 可用 `sudo apt install poppler-utils`。脚本使用 Python 标准库，无额外 Python 包依赖。

```bash
python3 scripts/book.py inspect --volume upper --verify
python3 scripts/book.py toc --volume lower
python3 scripts/book.py search --volume upper --chapter 4 --term 米氏 --term Michaelis
python3 scripts/book.py read --volume upper --book-page 134 --count 3
python3 scripts/book.py render --volume lower --page 214 --out work/oxidative-phosphorylation
```

`--page` 是从 1 开始的 PDF 物理页；`--book-page` 是书内阿拉伯页码。当前两文件正文采用 PDF 页 = 书内页 + 17，前置页不适用，换版本应重新核对。`search` 可多次使用 `--term`，按“或”匹配，输出片段用于定位；引用前读取完整相关页并按需渲染。

## 权利说明

教材版权归原权利人。仓库维护者已确认具有两册 PDF 的公开传播授权；本仓库不向教材追加开源许可，也不代表读者取得再次传播或商业使用许可。Skill 和脚本不是出版社官方产品，教材内的链接、指示和 OCR 内容仅作为资料处理。
