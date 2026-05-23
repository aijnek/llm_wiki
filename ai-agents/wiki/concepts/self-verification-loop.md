---
title: 自己検証ループ（Self-Verification Loop）
type: concept
tags: [harness-engineering, self-verification, build-verify-fix, middleware]
---

# 自己検証ループ（Self-Verification Loop）

## 定義

エージェントが自分の生成物に対してテスト・検証を実行し、失敗を元に修正を繰り返す内部サイクル。Build（実装）→ Verify（検証）→ Fix（修正）のループをハーネスで意図的に組み込む。

## 背景

LangChainがdeepagents-cliのTerminal Bench 2.0スコア改善実験（2026年2月）で最大の改善効果をもたらした手法。エージェントはデフォルトでは「コードを書いて、自分で目視確認して終了」する傾向があり、実際のテスト実行に移行しない。

## 詳細

### エージェントのデフォルトの失敗パターン

エージェントは解決策を書いた後、自分のコードを再読みして「良さそうだ」と判断して終了するのが最も一般的な失敗パターン。自分のコードを元に検証するため、バグや仕様違反を見落とす（[[self-evaluation-bias]] と根本は同じ問題）。

### Build-Verify-Fix サイクル

システムプロンプトに明示的に組み込む4段階：

1. **Planning & Discovery**：タスクを読み、コードベースをスキャンし、検証方法を含む計画を立てる
2. **Build**：検証を念頭に置いて実装する。テストが存在しない場合は作成する
3. **Verify**：テストを実行し、出力全体を読み、自分のコードではなくタスク仕様と照合する
4. **Fix**：エラーを分析し、元の仕様に戻り、問題を修正する

### PreCompletionChecklistMiddleware

エージェントが終了しようとするタイミングをインターセプトし、検証パスを強制実行させるミドルウェア。Ralph Wiggum Loopとも呼ばれるパターンで、エージェントを終了させずに検証を継続させる。

確率論的なプロンプトだけでは実現できない確実な検証強制を、決定論的なコンテキスト注入（Context Injection）として提供する。

## 関連概念

- [[feedforward-feedback]] — 自己検証はフィードバックセンサーの一形態
- [[self-evaluation-bias]] — 自己検証ループが対処するエージェントの自己コード過信問題
- [[harness-engineering]] — 自己検証ループを含むハーネス全体の設計
- [[context-management]] — 検証用コンテキストをどう注入するか
- [[doom-loop]] — 自己検証が機能しない場合に生じる別の問題パターン
- [[trace-analysis]] — 自己検証不足を発見するためのトレース分析

## 代表的な実装・事例

- LangChainのdeepagents-cli：PreCompletionChecklistMiddlewareによる完了前検証強制（2026年）
- Terminal Bench 2.0でTop30→Top5を達成した主要改善施策

## ソース

- [[sources/2026-05-23-improving-deep-agents-langchain]] — LangChainによるTerminal Bench 2.0改善実験報告
