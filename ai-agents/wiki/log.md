---
title: 操作ログ
type: log
---

# 操作ログ

> このファイルはappend-onlyです。エントリは削除・修正しません。
> 検索: `grep "^## \[" log.md` で全エントリ一覧

---

## [2026-05-23] init | Wiki初期化

- 作成: wiki/index.md, wiki/log.md, wiki/overview.md
- 作成: wiki/concepts/, wiki/entities/, wiki/sources/ ディレクトリ
- メモ: AIエージェントテーマのwikiを初期化

---

## [2026-05-23] ingest | Harness design for long-running application development

- 作成: wiki/sources/2026-05-23-harness-design-long-running-apps.md
- 作成: wiki/concepts/generator-evaluator-pattern.md
- 作成: wiki/concepts/context-anxiety.md
- 作成: wiki/concepts/self-evaluation-bias.md
- 作成: wiki/concepts/sprint-contract.md
- 作成: wiki/entities/anthropic.md
- 作成: wiki/entities/claude-agent-sdk.md
- 更新: wiki/concepts/harness-engineering.md, wiki/concepts/context-management.md, wiki/index.md
- メモ: AnthropicのPrithvi RajasekaranによるGAN着想のGenerator-Evaluatorアーキテクチャ。コンテキスト不安・自己評価バイアスという2つの根本問題を特定し、3エージェント構造（プランナー・ジェネレーター・エバリュエーター）で対処。Opus 4.6移行でハーネスを大幅に単純化した実例も含む

---

## [2026-05-23] ingest | Harness Engineering for Coding Agent Users

- 作成: wiki/sources/2026-05-23-harness-engineering-coding-users.md
- 作成: wiki/concepts/feedforward-feedback.md
- 作成: wiki/concepts/computational-vs-inferential.md
- 作成: wiki/concepts/harness-categories.md
- 作成: wiki/concepts/harnessability.md
- 更新: wiki/concepts/harness-engineering.md, wiki/index.md
- メモ: Birgitta Böckeler（ThoughtWorks）によるMartinFowler.com記事。ユーザーハーネスの体系化：フィードフォワード/フィードバックの2方向、Computational/Inferentialの2タイプ、保守性・アーキテクチャ適合性・振る舞いの3規制カテゴリ、ハーネス適合性（Harnessability）の概念を整理。振る舞いハーネスが最大の未解決課題として指摘

---

## [2026-05-23] ingest | Improving Deep Agents with Harness Engineering

- 作成: wiki/sources/2026-05-23-improving-deep-agents-langchain.md
- 作成: wiki/concepts/self-verification-loop.md
- 作成: wiki/concepts/trace-analysis.md
- 作成: wiki/concepts/doom-loop.md
- 作成: wiki/concepts/reasoning-sandwich.md
- 作成: wiki/entities/langchain.md
- 更新: wiki/concepts/harness-engineering.md, wiki/index.md
- メモ: LangChain（Vivek Trivedi）による定量的実証。モデル固定でハーネスのみ改善してTerminal Bench 2.0スコアを52.8%→66.5%（Top30→Top5）に向上。自己検証ループの強制化が最大の改善要因。Trace Analyzerスキル・LoopDetectionMiddleware・推論サンドイッチ（xhigh-high-xhigh）の3手法が核心

---

## [2026-05-23] ingest | ハーネスエンジニアリング：エージェントファーストの世界における Codex の活用

- 作成: wiki/sources/2026-05-23-harness-engineering-codex.md
- 作成: wiki/concepts/harness-engineering.md
- 作成: wiki/concepts/agents-md.md
- 作成: wiki/concepts/context-management.md
- 作成: wiki/concepts/agent-legibility.md
- 作成: wiki/concepts/entropy-management.md
- 作成: wiki/concepts/agentic-development-loop.md
- 作成: wiki/entities/openai.md
- 作成: wiki/entities/openai-codex.md
- 更新: wiki/index.md, wiki/overview.md
- メモ: OpenAIによる「手書きコード禁止」実験の実践報告。ハーネスエンジニアリングという新概念とその周辺概念を網羅的にingest

---

## [2026-05-23] ingest | LLMの指示追従能力

- 作成: wiki/sources/2026-05-23-llm-instruction-following.md
- 作成: wiki/concepts/instruction-following.md
- 作成: wiki/concepts/state-machine-tasks.md
- 作成: wiki/concepts/model-hacking-tendency.md
- 作成: wiki/entities/qwen.md
- 更新: wiki/concepts/harness-engineering.md, wiki/index.md, wiki/overview.md
- メモ: ユーザー個人によるQwen3.5/Claudeシリーズ比較実験メモ。7難易度タスク×6モデルで指示追従の境界を観察。状態遷移系タスクとLLMの親和性・状態出力ハーネスによる補完・モデルのルールハック傾向（別モデルに判断委譲の必要性）の3知見が核心

---

## [2026-05-23] ingest | エージェントタイプによってAskUserQuestionの価値は異なる

- 作成: wiki/sources/2026-05-23-ask-user-question-agent-types.md
- 作成: wiki/concepts/ambient-agent.md
- 作成: wiki/concepts/ask-user-question.md
- 作成: wiki/concepts/human-in-the-loop.md
- 更新: wiki/concepts/harness-engineering.md, wiki/index.md, wiki/overview.md
- メモ: ユーザーとDia（AIアシスタント）の対話メモ。チャット起点型 vs Ambient Agent（イベントトリガー型）という分類軸を導入し、エージェントタイプによってAskUserQuestionの価値と実装パターンが根本的に異なることを整理。Ambient型では「構造化された介入イベント」として疎結合なhuman-in-the-loopフローを実現できるという知見が核心

---

## [2026-05-23] lint | 定期ヘルスチェック

- 修正: wiki/overview.md — source_count を1→4に更新、後続3件のソース（Anthropic, Böckeler, LangChain）からの知見（Generator-Evaluator, フィードフォワード/フィードバック, ハーネス規制カテゴリ比較, LangChainの定量的効果, ハーネスとモデル能力の関係）を追記
- 修正: .claude/commands/ingest.md — Step 4.5としてoverview.md更新ステップを追加（source_countのインクリメントとコンテンツ更新を明示）
- 提案: Birgitta Böckeler（ThoughtWorks）エンティティページの作成（ソース記事著者・複数概念の提唱者だがページ未作成）
- 提案: ステアリングループ（Steering Loop）の専用概念ページ作成（harness-engineering.mdで言及されているがリンクなし）
- 検出（未修正）: harness-engineering.md・context-management.mdの"Opus 4.5"表記（context-anxiety.mdでは"Claude Sonnet 4.5"と記載、矛盾あり）
- 検出（未修正）: context-management.mdの"Claude Agent SDK"2か所がObsidianリンク未使用
