<p align="center">
  <img src="assets/logo.png" alt="Music2Taiko logo" width="220">
</p>

# Music2Taiko

中文 | [English](README.en.md) | [日本語](README.ja.md)

**Convert any music to Taiko TJA.**

Music2Taiko 是一个 Python 工具包和谱面制作工作流，用来把 MP3/WAV/OGG 音乐转换成可编辑、可测试的太鼓风格 `.tja` 初稿。它不会直接把全曲 onset 粗暴映射成 note，而是先生成可检查的 `drum_events[]` 中间层，再从 `tja-wiki` 检索相似曲和参考谱面证据，最后生成 OpenTaiko 可用的 TJA package。

这个项目的目标不是“一键生成最终发布谱面”，而是给谱面作者一个更强的起点：源曲鼓点锚点、四档难度设计、相似谱面 pattern 参考、TJA 导出，以及方便复盘的中间产物。

## 为什么现在需要 tja-wiki

早期流程主要是从鼓点事件生成简单的 `don` / `ka`。现在的流程加入了本地 TJA 知识库：

- `tja-wiki/` 保存从已有 TJA + OGG 谱面包中提取出的紧凑知识。
- 新歌会根据 BPM、事件密度、时长、节奏特征和 pattern 证据检索相似曲。
- LLM/skill 层使用 wiki 来判断“类似节奏应该如何设计 pattern”，但不会复制其它谱面的时间轴。
- Python 负责确定性部分：音频分析、`drum_events[]`、候选 timing anchors、pattern 落点、TJA 导出和 `aligned_samples`。
- TJA 导出支持四档难度，并支持普通音符、大音符、roll、balloon 等 TJA note 类型。

## 工作流

```text
新歌音频
  -> 音频转换 / 鼓点分析
  -> drum_events[] + candidate timing anchors
  -> 从 tja-wiki 检索相似曲和参考 pattern
  -> skill/LLM 生成 pattern_plan
  -> Python 把 pattern 落到源曲 drum_events 上
  -> 导出 easy / normal / hard / oni 四档 TJA
  -> OpenTaiko package: .tja + .ogg + 复盘文件
```

核心原则：note 必须忠于源曲鼓点；wiki 只用来帮助判断谱面语言、密度、难度递进和 pattern 设计。

## 安装

```powershell
python -m pip install -e .
```

依赖写在 `pyproject.toml`：

```text
librosa
numpy
soundfile
demucs
```

Demucs 是可选的上游 drum stem 工具，不是 TJA 生成流程的硬依赖。

## 快速开始

生成四档难度 TJA package：

```powershell
music2taiko create-tja ".\song.ogg" --out opentaiko_out --difficulties easy,normal,hard,oni
```

也可以用 module 方式运行：

```powershell
python -m music2taiko create-tja ".\song.ogg" --out opentaiko_out --difficulties easy,normal,hard,oni
```

当歌曲名过长时，使用短 ID，避免游戏加载路径过长：

```powershell
music2taiko create-tja ".\Very Long Song Name.mp3" --out opentaiko_out --song-id 001 --title "Very Long Song Name"
```

如果已经有 `arrangement_context.json`，可以跳过重新音频分析：

```powershell
music2taiko create-tja ".\song.ogg" --out opentaiko_out --reuse-context ".\opentaiko_out\song\arrangement_context.json"
```

如果已经由 skill/LLM 写好了 `pattern_plan.json`：

```powershell
music2taiko create-tja ".\song.ogg" --out opentaiko_out --pattern-plan ".\pattern_plan.json"
```

## 输出文件

`create-tja` 会生成 OpenTaiko 可用的目录：

```text
opentaiko_out/
  <safe-song-id>/
    <safe-song-id>.tja
    <safe-song-id>.ogg
    retrieval.json
    arrangement_context.json
    pattern_plan.json
    aligned_samples.json
```

关键文件：

- `retrieval.json`：从 `tja-wiki/corpus` 检索出的相似曲和参考证据。
- `arrangement_context.json`：BPM、鼓点摘要、密度窗口、候选锚点和检索上下文。
- `pattern_plan.json`：每个难度实际采用的谱面设计计划。
- `aligned_samples.json`：逐 note 记录生成 note 与源曲鼓点事件之间的对应关系。
- `.tja`：默认包含 `Easy`、`Normal`、`Hard`、`Oni` 四个 course。

## tja-wiki

`tja-wiki/` 是项目内的本地知识库：

```text
tja-wiki/
  corpus/
    manifest.json
    pattern_stats.json
    tja_summary.json
    audio_drum_event_summary.json
  01 OpenTaiko Chapter I/
  02 OpenTaiko Chapter II/
  03 OpenTaiko Chapter III/
```

它和原始 `database/` 分开。`database/` 可以很大、可以只放在本地；`tja-wiki/` 则保存更紧凑、可复用、适合检索和 LLM 阅读的谱面知识。

## 旧工作流

项目仍然保留早期调试和兼容导出命令：

```powershell
python -m music2taiko build-opentaiko ".\song.mp3" --out opentaiko_out --title "Song"
python -m music2taiko build ".\song.mp3" --out godot_out --title "Song"
python -m music2taiko generate ".\song.mp3" --out output\beatmaps --title "Song"
```

这些命令适合 PsyGodot JSON 调试、鼓点层检查和旧实验。新的 TJA 制作流程建议优先使用 `create-tja`。

## 开发

运行测试：

```powershell
python -m unittest discover -s tests
```

验证谱面制作 skill：

```powershell
python C:\Users\frued\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\tja-creator
```

项目结构：

```text
music2taiko/
  cli.py
  pipeline.py
  creator.py
  analysis/
  io/
  separation/
skills/tja-creator/
tja-wiki/
tests/
assets/logo.png
```

## 边界

Music2Taiko 是谱面初稿生成和分析工具。它不会替代人工谱师，但会把最耗时的起步工作结构化：提取源曲鼓点、检索相似谱面、生成四档难度、导出 TJA，并保留足够的复盘文件用于继续调整。
