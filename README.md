# LLM Wiki — AI Agents

LLM（Claude Code）が自律的に管理するパーソナルナレッジベース。生のソースを投入するとLLMが構造化されたWikiを構築・維持し続ける。

コアアイデアの詳細は [llm-wiki.md](llm-wiki.md) を参照。

## ディレクトリ構成

```
llm_wiki/
├── README.md          ← このファイル
├── llm-wiki.md        ← LLM Wikiパターンのアイデア原文
├── ai-agents/         ← AIエージェント分野のナレッジベース（ローカル版）
└── ai-agents-web/     ← ai-agentsのウェブサービス版（AWS Bedrock AgentCore）
```

## サブプロジェクト

### [ai-agents/](ai-agents/)

AIエージェント分野のパーソナルナレッジベース本体。Claude Codeをwikiライターとして使い、`raw/` に投入したソースから `wiki/` 以下の構造化Markdownを自動生成・更新する。ObsidianでVaultとして開くと便利。

スキル: `/ingest`（取り込み）、`/query`（質問）、`/lint`（ヘルスチェック）

### [ai-agents-web/](ai-agents-web/)

`ai-agents/` のウェブサービス版。`ai-agents/` は一切変更せず、スキル定義をAWS Bedrock AgentCore Runtime上で動かす。

**現在の状態（Phase 2.6 完了）**: AgentCore Runtime が ap-northeast-1 にデプロイ済み。S3 Files BYO で wiki/raw をマウントし、`./scripts/verify.sh --invoke` による AWS 上の疎通確認済み（6/6 passed）。次フェーズ: Lambda + WebSocket API（Phase 3）。
