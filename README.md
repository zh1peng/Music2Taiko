# Drum2Taiko

中文 | [English](README.en.md)

Drum2Taiko 是一个 Python 工具包，用来把 MP3/WAV 音乐转换成近似可玩的 Taiko 风格鼓面。它不是完整的“自动扒鼓谱”系统，而是先生成一个可检查的 `drum_events[]` 中间层，再把鼓点事件映射成 `don` / `ka` 谱面，并导出 PsyGodot `examples/rhythm_drum` 可以读取的 JSON。

当前项目还处于实验阶段，目标是给谱面作者一个可迭代的起点：自动生成初稿、查看报告、进 Godot 听手感，然后继续调 offset、鼓点质量、don/ka pattern 和难度密度。

## 工作流

```text
MP3/WAV 音频
  -> Demucs drum stem，优先使用
  -> librosa 鼓点/瞬态分析
  -> drum_events[] 中间层
  -> Taiko notes[]，包含 don/ka 和难度塑形
  -> PsyGodot rhythm_drum JSON
```

核心原则：

- 不直接把 full-mix onset 映射成 `don` / `ka`。
- `drum_events[]` 是音频分析和太鼓谱面之间的中间层。
- Demucs 是优先的 drum stem 来源，但谱面生成逻辑仍然属于 Drum2Taiko。
- PsyGodot JSON 是导出格式，不是包内部的数据中心。

## 当前能力

- 使用 Demucs 分离 drum stem。
- 使用 librosa 从 drum stem 中提取鼓点候选。
- 生成 `drum_events[]`，包含时间、量化时间、强度、粗分类、confidence、频段强度和 timing error。
- 生成 `easy` / `normal` / `hard` 三档 Taiko notes。
- normal 难度会回填过长空窗，避免中间长时间没有 note。
- normal 的 `don` / `ka` 使用固定短句 motif，而不是随机 shuffle。
- 导出 PsyGodot `rhythm_drum` 兼容 JSON。
- 生成 `review_report.json`，用于检查 offset、密度、最大空窗、don/ka 分布和 warning。

## 安装

开发模式安装：

```powershell
python -m pip install -e .
```

项目依赖写在 `pyproject.toml` 里，目前包括：

```text
librosa
numpy
demucs
```

如果要使用 CUDA 跑 Demucs，请先安装匹配你显卡和 CUDA 的 GPU 版 PyTorch，再安装本包。不要安装名为 `audio` 的 PyPI 包；它和 Demucs/音频分析没有关系，容易造成误解。

## 使用

完整生成流程，推荐用于 Godot 验证：

```powershell
python -m drum2taiko build ".\song.mp3" --out godot_out --title "Song"
```

这个命令会：

```text
1. 调用 Demucs 分离 drums
2. 从 drum stem 生成 drum_events[]
3. 生成 easy / normal / hard 三档谱面
4. 写出 review_report.json
```

只生成谱面，不主动跑 Demucs：

```powershell
python -m drum2taiko generate ".\song.mp3" --out output\beatmaps --title "Song"
```

显式使用 Demucs：

```powershell
python -m drum2taiko generate ".\song.mp3" --out output\beatmaps --title "Song" --use-demucs
```

Windows 上如果 Demucs 保存 WAV 遇到 TorchCodec/shared-FFmpeg 问题，可以输出 MP3 stem：

```powershell
python -m drum2taiko generate ".\song.mp3" --out output\beatmaps --title "Song" --use-demucs --demucs-device cuda --demucs-model htdemucs --demucs-segment 7 --demucs-format mp3
```

只做 Demucs 分离：

```powershell
python -m drum2taiko separate ".\song.mp3" --out stems --demucs-device cuda --demucs-model htdemucs --demucs-segment 7 --demucs-format mp3
```

使用已有 drum stem：

```powershell
python -m drum2taiko generate ".\song.mp3" --out output\beatmaps --title "Song" --drum-stem ".\drums.mp3"
```

## 输出文件

`build` 默认会生成：

```text
godot_out/
  <title>_easy.json
  <title>_normal.json
  <title>_hard.json
  review_report.json
  stems/
```

每个 beatmap JSON 包含：

- `drum_events[]`：可检查的鼓点事件层。
- `notes[]`：游戏用 note，包含 `time_sec`、`lane`、`window_ms`、`strength`、`subdivision`。
- `audio_offset_ms` / `chart_offset_ms`：音频和谱面偏移字段。
- `tempo_bpm`、`difficulty`、`drum_event_source` 等元数据。

## Report 怎么看

`review_report.json` 是当前最重要的调试入口。

重点字段：

- `offset_calibration`：基于 timing error 给出的全局 offset 参考。
- `notes`：该难度 note 数量。
- `avg_nps` / `peak_5s_nps`：平均和局部密度。
- `largest_note_gap_sec`：最大 note 空窗。
- `long_note_gaps`：超过阈值的长空窗列表。
- `lanes`：`don` / `ka` 数量。
- `lane_motif`：颜色切换率和最长同色 run。
- `warnings`：高密度、长空窗、没有 ka 等可疑点。

如果 Godot 里感觉“没踩在鼓点上”，优先检查：

```text
1. chart_offset_ms / audio_offset_ms
2. review_report.json 里的 timing error
3. drum_events[] 是否有误检或漏检
4. normal/hard 是否有过长空窗
5. don/ka pattern 是否符合手感
```

## 放进 PsyGodot

如果要把生成结果放进 PsyGodot 的示例工程，可以把生成的三档 JSON 复制到：

```text
E:\03_tools\psygodot\examples\rhythm_drum\beatmaps
```

例如当前《那天下雨了》对应的是 `song_002_*` 系列：

```text
song_002_easy.json
song_002_normal.json
song_002_hard.json
```

覆盖前建议先备份旧谱面，方便回听和对比。

## 开发

运行测试：

```powershell
python -m unittest discover
```

项目结构：

```text
drum2taiko/
  cli.py
  pipeline.py
  analysis/
    candidates.py
  separation/
    demucs.py
  io/
    psygodot.py
  review.py
tests/
skills/
pyproject.toml
```

## 设计边界

Drum2Taiko 当前不是：

- 完整真实鼓谱转写器。
- osu!/Taiko 官方谱面生成器。
- 一键生成最终可发布谱面的工具。

Drum2Taiko 当前更适合：

- 从音乐生成可编辑的太鼓谱面初稿。
- 研究 drum-event layer 到 Taiko chart layer 的映射。
- 给 PsyGodot rhythm game 示例快速生成测试谱面。
- 迭代 offset、密度、pattern 和难度塑形算法。
