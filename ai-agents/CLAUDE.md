# AI Agentsナレッジベース — Wikiスキーマ

このディレクトリはAIエージェント分野のパーソナルナレッジベースです。あなた（LLM）がwiki/以下のMarkdownファイルを作成・更新し、ユーザーはraw/にソースを投入してナレッジベースを育てます。

## 基本ルール

- **raw/** — 読み取り専用。ソースドキュメントを保管。LLMは読むだけで絶対に編集しない
- **wiki/** — LLMが管理するwikiページ群。ユーザーは読む専門
- **言語** — 全wikiページは日本語で書く。英語の固有名詞（ReAct, Tool Use, GPT等）はそのまま使う
- **Obsidianリンク** — `[[ページ名]]` 形式でクロスリファレンスを積極的に作る

---

## ディレクトリ構成

```
ai-agents/
├── CLAUDE.md               ← このファイル
├── raw/                    ← ソース（immutable）
│   ├── README.md
│   └── (ユーザーが投入するファイル)
└── wiki/                   ← Obsidian Vault ルート
    ├── index.md            ← 全ページカタログ
    ├── log.md              ← 操作ログ（append-only）
    ├── overview.md         ← 分野全体の俯瞰
    ├── concepts/           ← 概念ページ
    ├── entities/           ← エンティティページ（企業・人物・プロダクト）
    └── sources/            ← ソースサマリーページ
```

---

## ページ種別とフォーマット

### sources/ — ソースサマリー

ファイル名: `{YYYY-MM-DD}-{slug}.md`（例: `2026-05-23-react-paper.md`）

```markdown
---
title: (原題)
date: YYYY-MM-DD
type: source
source_type: article | paper | memo
url: (URLまたはファイルパス)
tags: [agent, tool-use, ...]
---

# (日本語タイトル)

## 要点
- (箇条書きで主要なポイント3〜7つ)

## 詳細サマリー
(2〜4段落の日本語要約)

## 関連ページ
- [[概念ページ名]]
- [[エンティティページ名]]
```

### concepts/ — 概念ページ

ファイル名: `{concept-name}.md`（例: `react.md`, `tool-use.md`）

```markdown
---
title: (概念名)
type: concept
tags: [...]
---

# (概念名)

## 定義
(1〜2文の簡潔な定義)

## 背景
(なぜこの概念が生まれたか、問題意識)

## 詳細
(技術的な説明)

## 関連概念
- [[関連概念1]] — 関係性の説明
- [[関連概念2]] — 関係性の説明

## 代表的な実装・事例
- (プロダクト名・論文名など)

## ソース
- [[source-slug]] — 一行説明
```

### entities/ — エンティティページ

ファイル名: `{entity-name}.md`（例: `openai.md`, `langchain.md`）

対象: 企業、研究者、プロダクト、フレームワーク

```markdown
---
title: (エンティティ名)
type: entity
entity_type: company | person | product | framework
tags: [...]
---

# (エンティティ名)

## 概要
(1〜3文の説明)

## AIエージェント分野での役割
(この分野における位置づけ・貢献)

## 代表的な成果・プロダクト
- (成果1)
- (成果2)

## 関連エンティティ
- [[関連エンティティ]]

## ソース
- [[source-slug]] — 一行説明
```

### overview.md — 分野俯瞰

AIエージェント分野全体のサマリー。ingestが積み重なるたびに更新する。フロンティアの整理、主要なアプローチの比較、未解決問題などを記述。

---

## index.md の形式

カテゴリ別に `- [[ページ名]] — 一行説明` の形式でリスト。

```markdown
## ソース (N件)
- [[sources/2026-05-23-react-paper]] — ReActフレームワークの原論文サマリー

## 概念 (N件)
- [[concepts/react]] — Reasoning + Acting の思考フレームワーク

## エンティティ (N件)
- [[entities/openai]] — AGI研究の最前線企業
```

---

## log.md の形式

append-only。各エントリは以下の形式:

```markdown
## [YYYY-MM-DD] ingest | ソースタイトル
- 作成: wiki/sources/xxx.md
- 更新: wiki/concepts/yyy.md, wiki/entities/zzz.md
- メモ: (特記事項があれば)
```

操作種別: `ingest` / `query` / `lint` / `init`

---

## ソース別 ingest 手順

### Web記事（Markdown）
`raw/` に保存されたMarkdownファイルをRead toolで読み込む。

### PDF（論文・レポート）
Claude CodeのRead toolでPDFを直接読み込む。ページ範囲が大きい場合は `pages` パラメータを使って重要部分を特定する。

### メモ・ノート
ユーザーが書いたMarkdownとして読み込む。ユーザーの視点・考察を尊重してサマリーに反映する。

---

## ingest時の品質基準

1. 1つのソースで**5〜15ページ**を更新する（サマリー1 + 概念・エンティティページ複数）
2. 新しい概念やエンティティが登場したら必ずページを作成する
3. 既存ページへの追記・修正を忘れない（新しい情報で古い記述を更新）
4. 矛盾する情報は両論を記載し、日付と出典を明記する
5. overview.mdは大きな知見が得られたときに更新する
