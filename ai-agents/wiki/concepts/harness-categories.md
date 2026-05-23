---
title: ハーネスの規制カテゴリ
type: concept
tags: [harness-engineering, maintainability, architecture-fitness, behaviour]
---

# ハーネスの規制カテゴリ

## 定義

エージェントハーネスが規制する対象の3分類。Birgitta Böckelerが提唱。保守性（Maintainability）・アーキテクチャ適合性（Architecture Fitness）・振る舞い（Behaviour）に分かれ、それぞれ難易度と利用可能ツールが大きく異なる。

## 背景

「ハーネス」という言葉が何を規制するのかを曖昧にしたまま議論すると、設計上の意思決定が困難になる。カテゴリを区別することで、どのコントロールが何を達成するのか・何を達成できないのかの議論を精密にできる。

## 詳細

### 保守性ハーネス（Maintainability）

内部コード品質と保守性を規制する。既存ツールが豊富で最も実装しやすいカテゴリ。

- **Computationalセンサーが確実に捕捉**：重複コード、循環複雑度、テストカバレッジ不足、アーキテクチャドリフト、スタイル違反
- **Inferentialセンサーが部分的に対応**：意味的な重複コード、冗長テスト、ブルートフォース修正、過剰設計
- **どちらも確実に捕捉できない**：問題の誤診断、過剰設計・不要機能の追加、指示の誤解（人間が仕様を明確化しない限り対処不可）

### アーキテクチャ適合性ハーネス（Architecture Fitness）

アプリケーションのアーキテクチャ特性を定義・検証する。ThoughtWorksのArchitecture Fitness Functionの概念に対応。

- パフォーマンス要件を定義するスキル（ガイド）とパフォーマンステスト（センサー）
- オブザーバビリティのコーディング規約（ガイド）とログ品質の振り返り（センサー）

### 振る舞いハーネス（Behaviour）

アプリケーションが機能的に正しく振る舞うかを規制する。現時点で最も未成熟なカテゴリ。

- **フィードフォワード**：機能仕様書（詳細度はケースによる）
- **フィードバック**：AIが生成したテストスイートの合否確認、カバレッジ計測、mutation testing
- **現状の限界**：AIが生成したテストへの信頼が根拠となっており、テストが正しい保証がない。approved fixturesパターンが一部で有効だが、汎用的な解決策はまだない
- **未解決問題**：人間が仕様を明確に定義しない限り、センサーによる機能的正しさの保証は困難

## 関連概念

- [[feedforward-feedback]] — 各カテゴリで使用するコントロールの方向性
- [[computational-vs-inferential]] — 各カテゴリで使用するコントロールの実行タイプ
- [[harness-engineering]] — 全カテゴリを包括するエンジニアリング活動
- [[harnessability]] — コードベースによってカテゴリごとの実装難易度が異なる
- [[entropy-management]] — 保守性ハーネスの継続的運用の一側面

## ソース

- [[sources/2026-05-23-harness-engineering-coding-users]] — Birgitta BöckelerによるMartinFowler.comの詳細記事
