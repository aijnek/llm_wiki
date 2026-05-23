---
title: Human-in-the-Loop
type: concept
tags: [human-in-the-loop, hitl, oversight, ambient-agent, ask-user-question]
---

# Human-in-the-Loop

## 定義

AIエージェントのワークフローに人間の判断・承認・修正を組み込むパターン。完全自律実行と完全手動作業の中間に位置し、重要な判断ポイントや不確実性が高い箇所で人間が介入できる設計を指す。

## 背景

エージェントの自律性が高まるにつれ、「どこで人間が関与するか」の設計が重要になった。完全自律はリスクが高く、完全手動は効率を損なう。Human-in-the-Loopは、エージェントの処理能力を活かしながら人間の判断を最も価値ある箇所に集中させる設計思想である。

## 詳細

### 実装パターン

**インライン承認型**  
エージェントがアクションを実行する前に毎回確認を求める。リスクが高い操作（本番環境への適用、外部送信等）に適する。処理速度とのトレードオフがある。

**例外介入型（Ambient Agent型）**  
デフォルトは自律処理し、特定の条件（閾値超過・不確実性の高い分岐・高リスク操作）のみ人間に通知する。[[ambient-agent]]において最も自然な形態。[[ask-user-question]]のような構造化インターフェースと組み合わせることで疎結合な実装が可能になる。

**事後レビュー型**  
エージェントが処理を完了した後に人間がレビューし、問題があれば差し戻す。CI/CDのPRレビューがこのモデルに近い。

### イベント駆動のhuman-in-the-loop

[[ambient-agent]]文脈で特に有効な形態。エージェントが処理を中断せずに「判断要求イベント」を発行し、ユーザーの非同期な回答を受けて処理を再開する。アプリ側のUI・通知レイヤーとエージェントの処理レイヤーが疎結合に保たれる。

### ハーネスエンジニアリングとの関係

Human-in-the-Loopは[[harness-engineering]]の「振る舞いカテゴリ」（[[harness-categories]]参照）に属するハーネスの一形態。エージェントがどのように機能するかを規制するのではなく、エージェントと人間の協働ポイントを設計する。

「人間の判断が最も効果を発揮する領域」の特定が、Human-in-the-Loopの設計における核心的な問いである（[[overview]]の未解決問題参照）。

## 関連概念

- [[ambient-agent]] — イベント駆動のhuman-in-the-loopが最も機能するエージェントタイプ
- [[ask-user-question]] — Ambient Agentにおける構造化された介入インターフェース
- [[harness-engineering]] — エージェントの自律実行に人間の判断を組み込む設計全般
- [[harness-categories]] — 振る舞いハーネスの分類においてHITLが位置づけられる
- [[generator-evaluator-pattern]] — Evaluatorを別エージェントにする形のhuman-not-in-the-loop設計

## ソース

- [[sources/2026-05-23-ask-user-question-agent-types]] — エージェントタイプとAskUserQuestionの価値、イベント駆動のhuman-in-the-loop
