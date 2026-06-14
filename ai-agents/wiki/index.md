---
title: Index
type: index
---

# AIエージェント Wiki — インデックス

> このファイルはLLMが管理します。ingestのたびに自動更新されます。

---

## ソース (7件)

- [[sources/2026-05-23-harness-engineering-codex]] — OpenAIによるエージェントファースト開発の実践：手書きコード禁止で100万行を構築
- [[sources/2026-05-23-harness-design-long-running-apps]] — AnthropicによるGenerator-Evaluatorアーキテクチャと長時間実行ハーネスの実験報告
- [[sources/2026-05-23-harness-engineering-coding-users]] — Birgitta Böckelerによるユーザーハーネスのフレームワーク化（フィードフォワード/フィードバック・3規制カテゴリ）
- [[sources/2026-05-23-improving-deep-agents-langchain]] — LangChainがハーネスのみでTerminal Bench 2.0 Top30→Top5を達成した定量的実証
- [[sources/2026-05-23-llm-instruction-following]] — Qwen3.5/Claudeシリーズで7タスク×6モデルの指示追従能力境界を観察した個人実験メモ
- [[sources/2026-05-23-ask-user-question-agent-types]] — エージェントタイプによってAskUserQuestionの価値が変わるというメモ（チャット型 vs Ambient型）
- [[sources/2026-06-13-when-ai-builds-itself]] — Anthropic Instituteによる再帰的自己改善レポート：タスクホライズン倍増・80%+コード自動化・3つの未来シナリオ

---

## 概念 (26件)

- [[concepts/recursive-self-improvement]] — AIが自分自身の後継を完全自律的に設計・開発する能力とその到達までの段階
- [[concepts/task-horizon]] — METRが測定するAI能力指標：50%信頼性でこなせるタスクの所要時間（4ヶ月ごとに倍増中）
- [[concepts/harness-engineering]] — AIコーディングエージェントが機能するための環境・スキャフォールド・フィードバックループの設計
- [[concepts/feedforward-feedback]] — ハーネスの2方向コントロール：ガイド（フィードフォワード）とセンサー（フィードバック）
- [[concepts/computational-vs-inferential]] — 決定論的・高速なCPU処理と確率論的・高コストなGPU処理のコントロール区分
- [[concepts/harness-categories]] — ハーネスの規制対象の3分類：保守性・アーキテクチャ適合性・振る舞い
- [[concepts/harnessability]] — コードベースのハーネス構築しやすさ。グリーンフィールドとレガシーで大きく異なる
- [[concepts/self-verification-loop]] — Build-Verify-Fixサイクルの強制化。エージェントの自己目視終了を防ぐ
- [[concepts/trace-analysis]] — エージェントトレースの自動分析によるハーネス反復改善
- [[concepts/doom-loop]] — 同一アプローチを10回以上繰り返すエージェントの停滞状態と検出手法
- [[concepts/reasoning-sandwich]] — 計画・検証フェーズにxhigh、実装フェーズにhigh推論予算を配分する戦略
- [[concepts/agents-md]] — エージェントへの指示ファイル：百科事典ではなく目次として設計する哲学
- [[concepts/context-management]] — エージェントのコンテキストウィンドウに何をいつどのように提供するかの設計
- [[concepts/agent-legibility]] — エージェントがシステムを直接認識・推論・検証できる状態を整備すること
- [[concepts/entropy-management]] — エージェント生成コードのアーキテクチャドリフトを継続的に解消する仕組み
- [[concepts/agentic-development-loop]] — 設計から運用までをエージェントがほぼ自律的に実行する開発サイクル
- [[concepts/generator-evaluator-pattern]] — GAN着想のジェネレーター・エバリュエーター分離によるフィードバックループアーキテクチャ
- [[concepts/context-anxiety]] — コンテキスト上限に近づくとエージェントが早期終了する現象とその対処
- [[concepts/self-evaluation-bias]] — エージェントが自分の出力を過大評価する傾向と独立評価エージェントによる解決
- [[concepts/sprint-contract]] — 実装前にジェネレーターとエバリュエーターが「完了の定義」を合意する仕組み
- [[concepts/instruction-following]] — LLMが複雑なルールを複数ターンにわたって正確に追従し続ける能力
- [[concepts/state-machine-tasks]] — 状態を持ちながら判断を続けるタスクと自己回帰モデルの親和性
- [[concepts/model-hacking-tendency]] — ロジックには追従しながら判断部分を恣意的に操作するモデルの傾向
- [[concepts/ambient-agent]] — イベントトリガーでバックグラウンド動作し、必要時のみ人間に介入を求めるエージェント
- [[concepts/ask-user-question]] — エージェントがユーザーへの質問をツールコールとして構造化するインターフェース
- [[concepts/human-in-the-loop]] — AIワークフローに人間の判断・承認を組み込むパターン

---

## エンティティ (7件)

- [[entities/openai]] — AGI研究の最前線企業、Codex・ChatGPT等を開発
- [[entities/openai-codex]] — OpenAIのAIコーディングエージェント、手書きコード不要の開発を実現
- [[entities/anthropic]] — Claude・Claude Codeを開発するAI安全性研究企業（2026年時点でコードの80%以上をAIが自動生成）
- [[entities/anthropic-institute]] — Anthropicの政策・社会影響研究部門、再帰的自己改善レポートを発行
- [[entities/claude-agent-sdk]] — Anthropicが提供するマルチエージェントシステム構築SDK
- [[entities/langchain]] — LangSmith・LangGraph・deepagents-cliを提供するエージェントフレームワーク
- [[entities/qwen]] — Alibaba Cloudが開発するオープンソースLLMシリーズ（4B/9B/27B等）

---

## その他のページ

- [[overview]] — AIエージェント分野の俯瞰
- [[log]] — 操作ログ
