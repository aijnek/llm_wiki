---
title: "Harness Engineering for Coding Agent Users"
date: 2026-05-23
type: source
source_type: article
url: https://martinfowler.com/articles/harness-engineering.html
tags: [harness-engineering, feedforward, feedback, computational, inferential, coding-agent]
---

# コーディングエージェントユーザーのためのハーネスエンジニアリング

## 要点

- ハーネスはbounded contextによって意味が異なる：モデル層・エージェントビルダー層・ユーザー層の3層構造
- コントロールには「ガイド（フィードフォワード）」と「センサー（フィードバック）」の2方向がある
- 実行タイプは「Computational（決定論的・高速）」と「Inferential（確率論的・高コスト）」の2種類
- ステアリングループ：問題が繰り返されるたびに人間がハーネスを反復改善する
- フィードバックは開発ライフサイクルの早い段階に配置するほど修正コストが低い（Shift Left）
- ハーネスの規制カテゴリ：保守性・アーキテクチャ適合性・振る舞いの3つ
- コードベースの「ハーネス適合性（Harnessability）」はグリーンフィールドとレガシーで大きく異なる

## 詳細サマリー

Birgitta Böckeler（ThoughtWorks）がMartinFowler.comに寄稿したこの記事は、コーディングエージェントのユーザー視点からハーネスエンジニアリングを体系化した。ハーネスはモデル層（LangChainの定義）・エージェントビルダー層・ユーザー層の3つのbounded contextで異なる意味を持つことを整理し、ユーザーが構築できるアウターハーネスに焦点を当てる。

ハーネスのコントロールは方向性（ガイド＝フィードフォワード、センサー＝フィードバック）と実行タイプ（Computational＝決定論的・高速、Inferential＝確率論的・GPU使用）の2軸で分類される。テスト・リンター・型チェッカーはComputationalセンサーであり、毎コミットに安価に実行できる。LLMコードレビューはInferentialセンサーであり、コストが高く非決定論的だがセマンティックな判断が可能。

ステアリングループとは、問題が繰り返されるたびに人間がガイドとセンサーを改善する継続的プロセスである。コーディングエージェント自身がカスタムリンターの記述や構造テストの生成を補助できるため、ハーネス構築のコストも低下している。フィードバックは開発ライフサイクルの早期（コミット前→PR前→CI）に配置する「Shift Left」が品質維持のコスト効率を高める。

ハーネスの規制カテゴリは保守性（既存ツールが豊富で最も実装しやすい）・アーキテクチャ適合性（Fitness Functionとして定義）・振る舞い（AIが生成したテストへの依存だけでは信頼性が不十分で最も未成熟）の3つ。振る舞いハーネスが最大の未解決課題として挙げられている。

## 関連ページ

- [[concepts/harness-engineering]]
- [[concepts/feedforward-feedback]]
- [[concepts/computational-vs-inferential]]
- [[concepts/harness-categories]]
- [[concepts/harnessability]]
- [[concepts/context-management]]
