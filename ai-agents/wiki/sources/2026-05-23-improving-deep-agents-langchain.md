---
title: "Improving Deep Agents with Harness Engineering"
date: 2026-05-23
type: source
source_type: article
url: https://www.langchain.com/blog/improving-deep-agents-with-harness-engineering
tags: [harness-engineering, deep-agents, self-verification, tracing, langchain]
---

# ハーネスエンジニアリングによるDeep Agentsの改善（LangChain）

## 要点

- LangChainのdeepagents-cliをTerminal Bench 2.0でTop30→Top5（52.8%→66.5%）に改善、モデルは固定
- ハーネスの3つのノブ：システムプロンプト、ツール、ミドルウェア
- Trace Analyzerスキル：LangSmithのトレースを並列エージェントで自動分析し、ハーネス改善提案を生成
- 自己検証ループ（Build-Verify-Fix）とPreCompletionChecklistMiddlewareによる完了前検証の強制
- LocalContextMiddlewareによる環境情報（ディレクトリ・ツール・タイムバジェット）の自動注入
- LoopDetectionMiddlewareによるDoomループ（同一ファイルへの過多な編集）の検出と回避
- 推論サンドイッチ（xhigh-high-xhigh）：計画と検証に高推論、実装に中推論を配分

## 詳細サマリー

LangChainのVivek Trivediが報告したこの実験では、deepagents-cli（コーディングエージェント）のハーネスのみを改善し、モデル（gpt-5.2-codex）を変えずにTerminal Bench 2.0のスコアを13.7ポイント向上させた。「ハーネスを変えるだけでTop30からTop5へ」という結果は、ハーネスエンジニアリングの効果を定量的に示す好例として引用価値が高い。

Trace Analyzerスキルは、LangSmithに蓄積されたエラートレースを並列エージェントで分析し、改善提案をメインエージェントが統合するブースティング的な手法。毎実験ループで「なぜ失敗したか」を自動分析することで、ハーネス改善の反復速度を大幅に向上させた。ただしタスクへの過学習（オーバーフィット）リスクがあり、変更後は回帰テストとの照合が必要。

最大の改善要因は自己検証ループの強制化。エージェントはデフォルトで「コードを書いて、目視確認して終了」する傾向があるが、PreCompletionChecklistMiddlewareにより完了前に検証パスを強制実行するよう設計した。Build-Verify-Fix（計画→実装→検証→修正）サイクルをシステムプロンプトに明示することで、テストを通じたヒルクライミングが可能になった。

LocalContextMiddlewareによる環境コンテキスト（カレントディレクトリ・ツール・タイムバジェット）の自動注入は、エージェントを新しい環境に「オンボーディング」させる重要な機能。LoopDetectionMiddlewareはDoomループ（同一ファイルへの過多な編集）を検出してアプローチの再考を促す。推論サンドイッチ（計画・検証時にxhigh、実装時にhigh）は、タイムアウト制約下での推論コストとパフォーマンスのバランスを最適化する手法。

## 関連ページ

- [[concepts/harness-engineering]]
- [[concepts/self-verification-loop]]
- [[concepts/trace-analysis]]
- [[concepts/doom-loop]]
- [[concepts/reasoning-sandwich]]
- [[entities/langchain]]
