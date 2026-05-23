---
title: OpenAI Codex
type: entity
entity_type: product
tags: [openai-codex, coding-agent, openai, agentic-development]
---

# OpenAI Codex

## 概要

OpenAIが開発・提供するAIコーディングエージェント。自然言語によるプロンプトからコードの生成・修正・テスト・レビュー・PRのオープンまでをエンドツーエンドで実行できる。CLI形式とAPIで提供される。

## AIエージェント分野での役割

「エージェントファーストのソフトウェア開発」の中心的なプレーヤー。単なるコード補完ツールではなく、標準的な開発ツール（gh・ローカルスクリプト・リポジトリ埋め込みスキル）を直接使用し、コンテキストを収集・活用しながら複雑な開発タスクを自律的に実行できる。

## 代表的な成果・プロダクト

- **ハーネスエンジニアリング実験（2025〜2026年）**: OpenAI社内でチーム3〜7名が手書きコード一切なしで約100万行のプロダクトを5ヶ月で構築。エンジニア1人あたり1日平均3.5 PRsのスループットを達成
- **GPT-5による動作**: Codex CLIはGPT-5を用いてコードを生成
- **長時間自律実行**: 単一タスクで6時間以上稼働する実行が日常的

### 主な機能

- コードベースの現状検証・バグ再現・修正
- プルリクエストのオープン・レビュー対応・マージ
- Chrome DevTools Protocolを使ったUIのテスト・動画記録
- LogQL/PromQLによるログ・メトリクスのクエリ
- AGENTS.mdに記述されたリポジトリ固有の指示への準拠

## 関連エンティティ

- [[openai]] — 開発元企業

## 関連概念

- [[harness-engineering]] — Codexを活用するための環境設計
- [[agents-md]] — CodexへのリポジトリレベルでのコンテキストおよびCodexへの指示ファイル
- [[agentic-development-loop]] — Codexが実現する自律開発ループ

## ソース

- [[sources/2026-05-23-harness-engineering-codex]] — OpenAIによるCodexを使ったエージェントファースト開発の実践報告
