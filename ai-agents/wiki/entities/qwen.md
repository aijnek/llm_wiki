---
title: Qwen（通義千問）
type: entity
entity_type: product
tags: [llm, open-source, alibaba, small-model]
---

# Qwen（通義千問）

## 概要

Alibaba Cloud（アリババクラウド）が開発するオープンソースのLLMシリーズ。Qwen3.5シリーズでは4B・9B・27B等のパラメータ規模のモデルを提供し、Ollama等を通じてローカル実行が可能。

## AIエージェント分野での役割

軽量・ローカル実行可能なLLMとして、ハーネスエンジニアリングの実験や比較評価に利用される。特に「小さなモデルではどこまでできるか」という境界観察に活用される。thinking機能（拡張推論）も持つが、`--think=false`フラグで無効化可能。

## 代表的な成果・プロダクト

- **Qwen3.5 4B**: 最小クラス。単純な繰り返しタスクは対応可能
- **Qwen3.5 9B**: 簡単な終了条件タスクで失敗が観察された
- **Qwen3.5 27B**: 条件分岐なしの終了条件タスクまで対応。単調増加判定などの複雑な条件で失敗
- **Ollamaでの利用**: `ollama run qwen3.5:4b --think=false` でthinkingなし実行が可能

## 関連エンティティ

- [[entities/anthropic]] — Claude（比較対象モデルの開発元）

## ソース

- [[sources/2026-05-23-llm-instruction-following]] — 指示追従能力観察実験でのQwen3.5の挙動記録
