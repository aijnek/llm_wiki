# raw/ — ソースドキュメント置き場

このディレクトリにAIエージェント関連のソースを投入してください。

## 対応フォーマット

| 種別 | 拡張子 | 用意方法 |
|------|--------|----------|
| Web記事 | `.md` | Obsidian Web Clipperでクリップ |
| 論文・レポート | `.pdf` | ダウンロードしてそのまま配置 |
| メモ・ノート | `.md` | 自分で書いて配置 |

## ingest方法

ファイルを配置したら、Claude Codeで `ai-agents/` をworking directoryとして開き:

```
/ingest <ファイル名>
```

または

```
/ingest
```

（引数なしの場合は未処理ファイルの一覧が表示されます）

## ルール

- このディレクトリ内のファイルはLLMが**読むだけ**で編集しません
- ファイルは削除・移動しないでください（logとの整合性が崩れます）
- サブディレクトリを作って整理しても構いません

## 画像のダウンロード（Obsidian使用時）

Obsidian Settings → Files and links → Attachment folder path を `raw/assets` に設定し、
クリップ後にホットキーで "Download attachments for current file" を実行すると画像もローカルに保存されます。
