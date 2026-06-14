---
title: "When AI builds itself"
date: 2026-06-13
type: source
source_type: article
url: https://www.anthropic.com/institute/recursive-self-improvement
tags: [recursive-self-improvement, anthropic, capability-trends, ai-productivity, governance]
---

# AIが自分自身をビルドするとき

## 要点

- タスクホライズン（AIが信頼できる水準でこなせるタスクの所要時間）が4ヶ月ごとに倍増しており、Claude Opus 3（4分）→ Sonnet 3.7（90分）→ Opus 4.6（12時間）と急増している
- 2026年5月時点でAnthropicがマージするコードの80%以上がClaudeが書いたもの。2024年はこの数値は一桁台だった
- Q2 2026のAnthropicエンジニア1人あたりのコードマージ量は2024年比8倍。Claude Codeのリリースと自律動作時間の延長という2つの変曲点が引き金
- 実験最適化でClaude Opus 4（2025年5月）は~3倍速を達成し、Claude Mythos Preview（2026年4月）は~52倍速を達成。熟練した人間研究者の4〜8時間かけた~4倍速を超えた
- 自律的なオープンエンド研究でも人間を上回る兆候：AI安全性の未解決問題を与えたところ、エージェントが800時間・$18,000で97%のパフォーマンスギャップを回復（人間2名は1週間で23%）
- 「現時点での人間の比較優位はまだ大きな絵を見ることと、目前のタスクの枠を超えて考えること」
- Anthropicは再帰的自己改善が可能になる前に国際的な検証体制と調整メカニズムを構築することを提唱

## 詳細サマリー

The Anthropic Instituteが発表した本レポートは、AIが自身の開発を加速しているという直接的な証拠を提示した。外部ベンチマーク（SWE-bench飽和、CORE-Bench飽和）と社内データの両面から、AIの能力が急速に向上していることを示す。タスクホライズンは4ヶ月ごとに倍増しており、2027年には数週間かかる作業をAIが担えるようになる可能性があるとしている。

Anthropic内部の定量データは特に注目に値する。2026年Q2には全マージコードの80%以上がClaudeが書いたもので、エンジニアはコードを打つ代わりに指示・レビューを担う役割に移行している。実験最適化ベンチマークでは1年以内にClaudeが人間の熟練研究者のパフォーマンスを大幅に上回るようになった。研究方向の選択においても、Mythos Previewが人間の判断を上回るケースが現れ始めており、「モデルが次に何をすべきかを人間より正確に提案できる」指標が向上中だ。

本記事は3つの可能な未来シナリオを提示する。①能力が頭打ちになるが現行AIが広く普及するケース、②AIラボが複利的な効率化を継続するケース（100人企業が10,000人企業の仕事をこなす）、③AIが完全な再帰的自己改善能力を獲得するケース。著者らは①は可能性が低く②か③が現実的と見ており、③においては進捗速度がコンピューティング供給量で決まる可能性があるとする。また「Amdahlの法則」として、速くなった部分がボトルネックを別の場所に移すだけという組織的な制約にすでに直面していることも指摘している。

## 関連ページ

- [[concepts/recursive-self-improvement]] — AIが自分自身の後継を自律的に開発する能力
- [[concepts/task-horizon]] — METRが測定するAIの能力指標（信頼できる水準でこなせるタスクの所要時間）
- [[entities/anthropic]] — レポートを発行したAnthropicとその内部データ
- [[entities/anthropic-institute]] — 本レポートの発行主体
- [[concepts/harness-engineering]] — Claudeを活用するエンジニアリングハーネスの設計
- [[concepts/agentic-development-loop]] — AIエージェントによる開発ループ
