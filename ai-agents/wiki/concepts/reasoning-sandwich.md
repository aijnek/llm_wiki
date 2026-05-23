---
title: 推論サンドイッチ（Reasoning Sandwich）
type: concept
tags: [harness-engineering, reasoning-budget, compute-optimization, adaptive-reasoning]
---

# 推論サンドイッチ（Reasoning Sandwich）

## 定義

エージェントの作業フェーズに応じて推論予算を変化させる戦略。計画フェーズと検証フェーズに高い推論予算（xhigh）、実装フェーズに中程度の推論予算（high）を割り当てる、サンドイッチ型の配分。

## 背景

LangChainがdeepagents-cliのTerminal Bench 2.0実験（2026年2月）で発見した最適化手法。推論モデルは自律的に数時間実行できるため、すべてのステップに最大推論予算を使うとタイムアウトや過剰コストが生じる。

## 詳細

### 推論予算の分配原則

gpt-5.2-codexの4段階（low/medium/high/xhigh）での実験結果：

- **計画フェーズ（xhigh）**：問題の全体理解が最重要。良い計画は後続の実装を効率化する
- **実装フェーズ（high）**：計画があれば中程度の推論で十分。常にxhighだとタイムアウトリスクが高まる
- **検証フェーズ（xhigh）**：ミスを確実に検出するために高い推論が必要

実験データ：全フェーズをxhighで実行すると53.9%（タイムアウト多発）、highのみだと63.6%、推論サンドイッチで66.5%。

### 適応的推論（Adaptive Reasoning）

モデル自身が各ステップで必要な推論量を自律的に決定する方向性。ClaudeとGeminiが実装済みであり、この機能が普及すると推論サンドイッチのような手動ヒューリスティックは不要になる可能性がある。

マルチモデルハーネスでは、計画に大型モデル→実装を小型モデルにハンドオフするアプローチも有効。

### 現在のモデル限界への対処

推論サンドイッチは[[doom-loop]]対策と同様に、現在のモデルの特性を前提としたヒューリスティックである。モデル能力の向上によって不要になる可能性があり、ハーネスを定期的に見直す際の対象となる。

## 関連概念

- [[harness-engineering]] — 推論予算配分もハーネス設計の一部
- [[self-verification-loop]] — 検証フェーズでxhigh推論を使う根拠
- [[trace-analysis]] — 推論予算の最適化根拠となるコスト・レイテンシデータ収集
- [[doom-loop]] — 実装フェーズで高すぎる推論予算がタイムアウトを引き起こす問題

## ソース

- [[sources/2026-05-23-improving-deep-agents-langchain]] — LangChainによるTerminal Bench 2.0改善実験報告
