---
title: LangChain
type: entity
entity_type: framework
tags: [langchain, langsmith, deep-agents, tracing, orchestration]
---

# LangChain

## 概要

AIエージェントの構築・オーケストレーション・観測のためのオープンソースフレームワーク群。LangChain（コアライブラリ）、LangGraph（グラフ型エージェントワークフロー）、LangSmith（トレーシング・評価プラットフォーム）を提供する。

## AIエージェント分野での役割

LangChainはエージェントのツール使用・メモリ管理・マルチエージェントオーケストレーションの標準化に大きく貢献。LangSmithはエージェントのトレース・評価・改善サイクルのインフラとして広く採用されている。deepagents-cliというオープンソースのコーディングエージェントも開発・公開しており、ハーネスエンジニアリングの実証実験も積極的に行っている。

## 代表的な成果・プロダクト

- **LangChain**：LLMアプリケーション構築のためのコアライブラリ（Python・JavaScript）
- **LangGraph**：ステートフルなマルチエージェントワークフローを構築するグラフ型フレームワーク
- **LangSmith**：エージェントトレーシング・評価・デバッグプラットフォーム。[[trace-analysis]]の基盤
- **deepagents-cli**：オープンソースのコーディングエージェント（Terminal Bench 2.0 Top5）
- **Trace Analyzerスキル**：LangSmithトレースを並列エージェントで自動分析してハーネス改善提案を生成するスキル

## 関連エンティティ

- [[entities/openai]] — deepagents-cliでgpt-5.2-codexを使用
- [[entities/anthropic]] — Claude Opus 4.6でのベンチマーク比較（59.6%）

## ソース

- [[sources/2026-05-23-improving-deep-agents-langchain]] — ハーネスエンジニアリングによるdeepagents改善実験報告
