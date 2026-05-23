---
title: Claude Agent SDK
type: entity
entity_type: product
tags: [claude-agent-sdk, anthropic, multi-agent, harness-engineering, sdk]
---

# Claude Agent SDK

## 概要

Anthropicが提供するマルチエージェントシステム構築のためのSDK。複数のAIエージェントを連携させるオーケストレーションを簡潔に記述でき、コンテキストの自動compactionなどの機能を提供する。

## AIエージェント分野での役割

[[generator-evaluator-pattern]]のようなマルチエージェントアーキテクチャをシンプルなコードで実装するための基盤を提供する。オーケストレーションの複雑さを抽象化し、開発者がエージェントの設計と指示に集中できるようにする。

Anthropic自身がこのSDKを用いて社内の実験的ハーネスを構築・公開しており、フロントエンドデザインスキルや長時間実行コーディングハーネスの実装がリファレンス事例となっている。

## 代表的な成果・プロダクト

- コンテキストの自動compaction（長時間実行エージェントのコンテキスト増大を自動管理）
- [[generator-evaluator-pattern]]のシームレスな実装サポート
- Anthropicの長時間実行コーディングハーネス実験での採用（プランナー・ジェネレーター・エバリュエーターの3エージェント構造）

## 関連エンティティ

- [[anthropic]] — 開発・提供元

## ソース

- [[sources/2026-05-23-harness-design-long-running-apps]] — Claude Agent SDKを用いた長時間実行ハーネス構築の実装報告
