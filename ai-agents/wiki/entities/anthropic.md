---
title: Anthropic
type: entity
entity_type: company
tags: [anthropic, claude, ai-safety, research, harness-engineering, recursive-self-improvement]
---

# Anthropic

## 概要

2021年設立のAI安全性研究企業。「信頼性が高く、解釈可能で、制御可能なAIシステムの構築」を使命とする。Claude（大規模言語モデル）シリーズおよびClaude Codeを開発・提供している。

## AIエージェント分野での役割

大規模言語モデルの研究開発に加え、AIエージェントの実用的な活用に関する工学的知見を積極的に公開している。ハーネスエンジニアリング、マルチエージェントアーキテクチャ、長時間実行エージェントの設計など、エージェントファースト開発の実践的な手法を社内実験を通じて検証し、エンジニアリングブログで報告している。

2026年時点では自社の開発プロセス自体がAI化の最前線であり、社内データを公開して業界全体の能力向上トレンドの透明性を高めている。

## 代表的な成果・プロダクト

- **Claude** — Opus / Sonnet / Haikuの各シリーズを展開するLLM（Opus 4.6, Mythos Previewが現在のフロンティア）
- **Claude Code** — Claude搭載のAIコーディングエージェント（CLIおよびIDEプラグイン）。2025年2月に研究プレビューとしてリリース
- **Claude Agent SDK** — マルチエージェントシステム構築のためのSDK
- **Anthropic Labs** — 新しいAI活用パターンを探索する社内チーム
- **The Anthropic Institute** — AI政策・社会影響を研究する部門
- 長時間実行エージェントハーネスの設計・実験報告（フロントエンドデザイン、フルスタック開発）
- Context Engineeringに関するエンジニアリングブログシリーズ

## 主要な定量データ（2026年時点）

- **コード自動化率**: マージコードの80%以上がClaude著（2026年5月）。Claude Codeリリース前（2025年2月以前）は一桁%台
- **生産性向上**: Q2 2026のエンジニア1人あたりコードマージ量が2024年比8倍
- **研究最適化**: 実験最適化ベンチマーク（カーネル最適化）でClaude Opus 4が~3倍速（2025年5月）→ Mythos Previewが~52倍速（2026年4月）。熟練人間研究者の~4倍速を大幅に超えた
- **オープンエンド研究**: AI安全性問題をエージェントが自律的に解決（800累積時間・$18,000でパフォーマンスギャップ97%回復、人間2名1週間では23%）

## 関連エンティティ

- [[claude-agent-sdk]] — Anthropicが提供するマルチエージェント構築SDK
- [[anthropic-institute]] — Anthropicの政策・社会影響研究部門

## ソース

- [[sources/2026-05-23-harness-design-long-running-apps]] — Anthropic Labsによる長時間実行アプリ開発ハーネスの実験報告
- [[sources/2026-06-13-when-ai-builds-itself]] — Anthropic Instituteによる再帰的自己改善・AI開発加速レポート
