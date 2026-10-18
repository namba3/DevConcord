# DevConcord

DevConcordは、設計・開発・レビューの共通資料、テンプレート、プロンプト、Agent Skillsを提供します。特定の技術スタックやエージェントを前提にせず、導入先の既存規約・規模・用途に合わせて必要な部分を選んで利用します。

## 目的から選ぶ

| 目的 | 入口 |
|---|---|
| はじめてDevConcordを使う | [導入と運用ガイド](docs/getting-started.md) |
| 設計書から新しいプロジェクトを始める | [Bootstrapプロンプト](prompts/bootstrap-from-design.md) |
| 既存プロジェクトへ規約を選んで導入する | [Adoptionプロンプト](prompts/adopt-guidance.md) |
| 導入済み資料を安全に更新する | [Synchronizationプロンプト](prompts/sync-guidance.md) |
| 共通原則・テンプレートを探す | [資料一覧](docs/README.md) |
| プロンプトを使う・選ぶ | [プロンプト一覧](prompts/README.md) |
| 特定タスク向けAgent Skillを選ぶ | [Skills一覧](prompts/README.md#agent-skills) |
| Skillsを導入・同期・検証する | [Agent Skills運用ガイド](docs/agent-skills.md) |
| ドキュメント体系を設計・改善する | [ドキュメント設計ガイド](docs/common/documentation-design.md) |

## 収録内容

- DDD、Self-documenting Code、SDD、DbC、TDD、Performance / Robustness / Replaceability by Design等の開発・設計ガイド
- 要求仕様、ADR、課題管理、リスク管理、完成度評価の規約とテンプレート
- READMEを含む文書設計、導入、更新、検証のための共通指針
- `AGENTS.md`・`REVIEWS.md`生成、Bootstrap、Adoption、Synchronization用プロンプト
- 複数エージェントで再利用するAgent Skillsと、安全な配布・同期スクリプト

## 適用方針

資料は初期値であり、導入先の文書構成、公開基盤、言語、リンク、ビルド、既存の課題・要求管理を調査したうえで選択適用します。小規模なCLIではREADMEと必要最小限の資料で十分なことがあり、大規模な製品では利用者・開発者・運用者ごとの案内や公開リファレンスが必要なことがあります。DevConcord固有のディレクトリ構成、README形式、品質評価軸を一律に強制しません。

## ライセンス

個別に異なるライセンスが明記されていない限り、このリポジトリの資料・テンプレート・プロンプトはMITまたはApache License 2.0のいずれかを選択して利用できます。詳細は[MIT License](LICENSE-MIT)と[Apache License 2.0](LICENSE-APACHE)を参照してください。
