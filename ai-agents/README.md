# AI Agents ナレッジベース

AIエージェント分野のパーソナルナレッジベース。Claude Codeがwiki以下のMarkdownファイルを作成・更新し、ソースを投入するたびに知識が積み重なる。

## 使い方

```bash
# ソースを raw/ に置いてから
/ingest   # ソースを読み込んでwikiに統合
/query    # wikiに蓄積された知識に質問する
/lint     # wikiのヘルスチェック（矛盾・孤立ページの検出）
```

ObsidianでVaultとして `wiki/` を開くと、グラフビューでページ間のつながりを確認できる。

## ディレクトリ構成

```
ai-agents/
├── CLAUDE.md          ← WikiスキーマとLLMへの指示
├── README.md          ← このファイル
├── raw/               ← ソースドキュメント（immutable・LLMは読むだけ）
└── wiki/              ← Obsidian Vault ルート（LLMが管理）
    ├── index.md       ← 全ページカタログ
    ├── log.md         ← 操作ログ（append-only）
    ├── overview.md    ← 分野全体の俯瞰
    ├── concepts/      ← 概念ページ
    ├── entities/      ← エンティティページ（企業・人物・プロダクト）
    └── sources/       ← ソースサマリーページ
```

## ソースの投入方法

1. `raw/` にファイルを置く（Markdown、PDF、メモなど）
2. Claude Codeで `/ingest` を実行
3. LLMがソースを読み、wiki以下の関連ページを自動更新する

ウェブ記事はObsidian Web Clipperでクリップすると便利。
