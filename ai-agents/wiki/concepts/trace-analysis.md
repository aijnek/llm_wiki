---
title: トレース分析（Trace Analysis）
type: concept
tags: [harness-engineering, tracing, observability, feedback-loop, langsmith]
---

# トレース分析（Trace Analysis）

## 定義

エージェントの入出力・ツール呼び出し・メトリクス（レイテンシ・トークン数・コスト）をトレースとして記録し、失敗パターンを自動分析してハーネスを改善する手法。

## 背景

LLMモデルはブラックボックスであり、内部メカニズムの解釈は困難。しかし入出力のテキストは観察可能であり、これをトレースとして収集・分析することでエージェントの失敗パターンを特定できる。LangChainがdeepagents-cliの改善実験で活用し、ハーネス改善の反復速度を大幅に向上させた。

## 詳細

### トレースの役割

- **デバッグ**：エージェントがどこで失敗したかの特定（推論エラー・指示への不従順・検証不足・タイムアウト等）
- **ツールと推論の同時デバッグ**：モデルが間違った方向に進む原因がツール不足か指示不足かを判別
- **コスト・レイテンシ計測**：推論予算配分（[[reasoning-sandwich]]）の最適化データ収集

### Trace Analyzerスキル（LangChain）

LangChainが開発した自動分析スキル：

1. LangSmithからトレースデータを取得
2. 並列エラー分析エージェントを起動 → メインエージェントが知見と改善提案を統合
3. 人間がフィードバックを検証し、ハーネスへの変更を適用

機械学習の「ブースティング」に類比できる：前回の失敗に焦点を当てて改善を反復する手法。

### 注意点：過学習リスク

特定タスクへの最適化（オーバーフィット）は他タスクへの汎化性能を低下させる回帰を引き起こす可能性がある。変更を加える際は複数タスクでの回帰テストとの照合が重要。

## 関連概念

- [[harness-engineering]] — トレース分析はハーネス改善の反復サイクルの核心
- [[feedforward-feedback]] — トレースはフィードバックセンサーの一形態
- [[self-verification-loop]] — トレース分析が特定する主要な失敗パターンの一つ
- [[doom-loop]] — トレース分析で発見される問題パターン
- [[reasoning-sandwich]] — トレースデータを元に最適化する推論予算配分
- [[entities/langchain]] — LangSmithとTrace Analyzerスキルの提供元

## 代表的な実装・事例

- LangSmith：LangChainのトレーシング・評価プラットフォーム
- Trace Analyzerスキル：LangChainによる自動ハーネス改善スキル（2026年公開予定）

## ソース

- [[sources/2026-05-23-improving-deep-agents-langchain]] — LangChainによるTerminal Bench 2.0改善実験報告
