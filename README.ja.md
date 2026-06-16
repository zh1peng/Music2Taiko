<p align="center">
  <img src="assets/logo.png" alt="Music2Taiko logo" width="220">
</p>

# Music2Taiko

[中文](README.md) | [English](README.en.md) | 日本語

**Convert any music to Taiko TJA.**

Music2Taiko は、MP3/WAV/OGG の楽曲から、編集可能でテストしやすい太鼓スタイルの `.tja` 譜面ドラフトを生成する Python パッケージ兼譜面制作ワークフローです。単純に全体の onset を note に変換するのではなく、まず確認可能な `drum_events[]` 中間レイヤーを作り、`tja-wiki` から似た楽曲や既存譜面の根拠を検索し、OpenTaiko で使える TJA package を出力します。

このプロジェクトは「ワンクリックで最終公開譜面を作る」ものではありません。譜面制作者に、より良い出発点を提供することを目的としています。具体的には、元楽曲に基づくドラムイベントのアンカー、4 段階の難易度設計、似た譜面の pattern 参照、TJA 出力、そして後から検証しやすい中間成果物を提供します。

## なぜ tja-wiki が必要か

初期の Music2Taiko は、主にドラムイベントから簡単な `don` / `ka` を生成していました。現在のワークフローでは、ローカルの TJA ナレッジベースを追加しています。

- `tja-wiki/` は、既存の TJA + OGG 譜面パックから抽出した軽量な知識を保存します。
- 新しい楽曲は、BPM、イベント密度、長さ、リズム特徴、pattern の根拠を使って似た楽曲を検索します。
- LLM/skill 層は wiki を使って「似たリズムならどのような pattern 設計が自然か」を判断しますが、他の譜面のタイムラインをコピーしません。
- Python は決定的な処理を担当します。音声解析、`drum_events[]`、候補 timing anchors、pattern の配置、TJA 出力、`aligned_samples` の生成です。
- TJA 出力は 4 段階の難易度に加えて、通常ノーツ、大音符、roll、balloon などの TJA note type を扱えます。

## ワークフロー

```text
新しい楽曲音声
  -> 音声変換 / ドラムイベント解析
  -> drum_events[] + candidate timing anchors
  -> tja-wiki から似た楽曲と参考 pattern を検索
  -> skill/LLM が pattern_plan を作成
  -> Python が pattern を元楽曲の drum_events に配置
  -> easy / normal / hard / oni の 4 コース TJA を出力
  -> OpenTaiko package: .tja + .ogg + 検証用ファイル
```

重要な原則は、生成される note が元楽曲のドラムイベントに忠実であることです。wiki は譜面表現、密度、難易度の進行、pattern 設計を助けるために使い、既存譜面をコピーするためには使いません。

## インストール

```powershell
python -m pip install -e .
```

依存関係は `pyproject.toml` に定義されています。

```text
librosa
numpy
soundfile
demucs
```

Demucs は任意の上流 drum stem ツールです。TJA 生成ワークフローの必須ランタイム依存ではありません。

## クイックスタート

4 段階の難易度を含む TJA package を生成します。

```powershell
music2taiko create-tja ".\song.ogg" --out opentaiko_out --difficulties easy,normal,hard,oni
```

module 形式でも実行できます。

```powershell
python -m music2taiko create-tja ".\song.ogg" --out opentaiko_out --difficulties easy,normal,hard,oni
```

楽曲名が長い場合は、ゲーム側の読み込み問題を避けるために短い ID を指定できます。

```powershell
music2taiko create-tja ".\Very Long Song Name.mp3" --out opentaiko_out --song-id 001 --title "Very Long Song Name"
```

既存の `arrangement_context.json` がある場合は、音声解析を再実行せずに再生成できます。

```powershell
music2taiko create-tja ".\song.ogg" --out opentaiko_out --reuse-context ".\opentaiko_out\song\arrangement_context.json"
```

skill/LLM が作成した `pattern_plan.json` を指定することもできます。

```powershell
music2taiko create-tja ".\song.ogg" --out opentaiko_out --pattern-plan ".\pattern_plan.json"
```

## 出力ファイル

`create-tja` は OpenTaiko で使えるディレクトリを生成します。

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

主なファイル:

- `retrieval.json`: `tja-wiki/corpus` から検索された似た楽曲と参考根拠。
- `arrangement_context.json`: BPM、ドラムイベント概要、密度ウィンドウ、候補アンカー、検索コンテキスト。
- `pattern_plan.json`: 各難易度で実際に使われる譜面設計計画。
- `aligned_samples.json`: 生成された note と元楽曲のドラムイベントの対応関係。
- `.tja`: デフォルトで `Easy`、`Normal`、`Hard`、`Oni` の 4 コースを含む TJA。

## tja-wiki

`tja-wiki/` はプロジェクト内のローカル知識ベースです。

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

これは元の `database/` とは分離されています。`database/` は大きく、ローカルにだけ置くことができます。一方で `tja-wiki/` は、検索や LLM が読みやすい形に圧縮された、再利用しやすい譜面知識を保存します。

## 旧ワークフロー

Music2Taiko には、以前のデバッグ用および互換出力用コマンドも残っています。

```powershell
python -m music2taiko build-opentaiko ".\song.mp3" --out opentaiko_out --title "Song"
python -m music2taiko build ".\song.mp3" --out godot_out --title "Song"
python -m music2taiko generate ".\song.mp3" --out output\beatmaps --title "Song"
```

これらは PsyGodot JSON のデバッグ、ドラムイベント層の確認、旧実験に役立ちます。新しい TJA 制作では `create-tja` を推奨します。

## 開発

テストを実行します。

```powershell
python -m unittest discover -s tests
```

譜面制作 skill を検証します。

```powershell
python C:\Users\frued\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\tja-creator
```

プロジェクト構成:

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

## スコープ

Music2Taiko は譜面ドラフト生成と解析のためのツールです。人間の譜面制作を置き換えるものではありませんが、元楽曲のドラムアンカー、コーパスに基づく pattern 参考、4 段階の難易度設計、TJA 出力、そして実用的な検証用ファイルを提供し、制作の出発点を大きく改善します。
