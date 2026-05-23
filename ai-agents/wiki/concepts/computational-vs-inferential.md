---
title: ComputationalとInferential
type: concept
tags: [harness-engineering, computational, inferential, control-type]
---

# ComputationalとInferential

## 定義

ハーネスのコントロール（ガイド・センサー）の実行タイプの区分。Computational（計算型）はCPUで実行される決定論的・高速な処理、Inferential（推論型）はGPU/NPUで実行される確率論的・高コストな処理。

## 背景

Birgitta Böckelerが提唱した分類。ハーネスを設計する際に「どのコントロールをどの場面で使うか」を判断するための軸として機能する。速さと信頼性（Computational）か、セマンティックな理解力（Inferential）かのトレードオフを明示化する。

## 詳細

### Computational（計算型）

- **特徴**：決定論的・高速・安価、CPU上で実行
- **代表例**：リンター、型チェッカー、ユニットテスト、アーキテクチャ制約テスト（ArchUnit）、dep-cruiser
- **適切な場面**：毎コミット・毎変更で実行する自動チェック。構造的な問題（重複コード・サイクロマティック複雑度・依存関係違反）の検出に確実
- **限界**：意味的な問題（意図的な設計ミス、指示の誤解）は検出できない

### Inferential（推論型）

- **特徴**：確率論的・低速・高コスト、GPU/NPUで実行
- **代表例**：AIコードレビュー（スキル）、LLM-as-judge、アーキテクチャレビューエージェント
- **適切な場面**：意味的な重複・過剰設計の検出など、セマンティックな判断が必要な場合。強力なモデルとの組み合わせで信頼性が上がる
- **限界**：コストが高いため毎コミットには使えない。非決定論的なので結果の保証がない

### 組み合わせの原則

- Computationalコントロールはコミット前・PR前に実行（常時実行できるほど安価）
- Inferentialコントロールはより高価なため、CIステップ以降や重要なチェックポイントで実行
- 同じ目的でも両タイプを組み合わせ可能（例：APIドキュメントをMarkdownとして参照するInferentialガイド + LSPで型情報をComputationalに提供）

### 振る舞い検証への応用の限界

AIが生成したテストスイートへの依存（Computational）だけでは機能的な正しさを保証できない。InferentialセンサーによるLLM-as-judgeも確率論的であり、どちらも確実な振る舞い保証は難しい。

## 関連概念

- [[feedforward-feedback]] — コントロールの方向性（ガイド vs センサー）
- [[harness-engineering]] — コントロールを設計・整備するエンジニアリング活動
- [[harness-categories]] — 保守性・適合性・振る舞いの各カテゴリでの使い分け
- [[self-evaluation-bias]] — Inferentialセンサーが対処するエージェントの自己評価過大問題

## 代表的な実装・事例

- Computational：ESLint, semgrep, ArchUnit, dep-cruiser, mutation testing
- Inferential：/code-reviewスキル, /architecture-reviewスキル

## ソース

- [[sources/2026-05-23-harness-engineering-coding-users]] — Birgitta BöckelerによるMartinFowler.comの詳細記事
