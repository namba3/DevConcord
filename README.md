# DevConcord

DevConcordは、設計・開発・レビューの共通資料、テンプレート、Agent Skillsを提供します。Agent Skillsを作業ワークフローの正本とし、特定の技術スタックやエージェントを前提にせず、導入先の既存規約・規模・用途に合わせて必要な部分を選んで利用します。

## 目的から選ぶ

初回利用時は、先に[実行例付きの導入ガイド](docs/getting-started.md)を開いてください。日々の開発では内部Skill名を選ぶ必要はありません。目的、対象、委任範囲、変更しない条件を伝えると、AIがリポジトリの課題表・指示・証拠から必要な作業手順と検証を選びます。承認が必要な要求・互換性・データ損失・セキュリティ・外部操作は人間の判断に残します。Agent Skillsはユーザー単位のUser Scopeが標準で、プロジェクトへのコピーはチーム共有・CI等のProject Scopeが必要な場合に選びます。ワークフロー作業は導入先リポジトリを作業コンテキストにし、DevConcordは読み取り専用の参照元として扱います。

| 目的 | 入口 |
|---|---|
| 次の課題・複数課題・ブロッカー対応・再開を依頼する | [開発クイックリファレンス](docs/common/ai-development-quick-reference.md)、[自然言語ルーター](.agents/skills/devconcord/references/routing.md) |
| 変更に必要な検証を選ぶ | [開発クイックリファレンスの検証案内](docs/common/ai-development-quick-reference.md#検証選択) |
| はじめてDevConcordを使う | [導入と運用ガイド](docs/getting-started.md) |
| 設計書から新規Bootstrapする / 既存プロジェクトへAdoptionする | [Bootstrapの実行例](docs/getting-started.md#3-設計書から新規bootstrapするcodex-cli)、[Adoptionの実行例](docs/getting-started.md#4-既存リポジトリへadoptionするcodex-cli) |
| 設計・開発・レビュー・診断・品質判断を行う | [`devconcord` Unified Skill](.agents/skills/devconcord/SKILL.md) と[コマンドルーター](.agents/skills/devconcord/references/routing.md) |
| リスク比例型の専門ワークフローを選ぶ | [Risk-Proportional Skill Application / Verification](docs/common/ai-assisted-development.md#175-リスク比例型skill適用と検証) |
| 共通原則・テンプレートを探す | [資料一覧](docs/README.md) |
| ローカルDevConcord資料を版固定で参照する | [`devconcord` Reference workflow](.agents/skills/devconcord/references/modules/management/devconcord-reference/module.md)、[参照運用](docs/agent-skills.md#ローカルdevconcord資料の参照) |
| Skill非対応環境で手動利用する | [Skill本体と参照資料を渡す方法](docs/agent-skills.md#skills非対応環境で手動利用) |
| User / Project Scopeへ導入・同期・移行する | [Skills運用ガイド](docs/agent-skills.md)、[Getting Started](docs/getting-started.md) |
| ドキュメント体系を設計・改善する | [ドキュメント設計ガイド](docs/common/documentation-design.md) |

## 収録内容

- DDD、Self-documenting Code、SDD、DbC、TDD、Performance / Robustness / Replaceability / Security / Observability by Design等の開発・設計ガイド
- 要求仕様、ADR、課題管理、リスク管理、完成度評価の規約とテンプレート
- READMEを含む文書設計、導入、更新、検証のための共通指針
- `AGENTS.md`・`REVIEW.md`生成、Bootstrap、Adoption、設計・開発オーケストレーション、影響評価、テスト設計、実装計画、課題駆動開発、Observability設計、原因分析、エージェント評価、互換性移行、リリース、依存ガバナンス、Synchronization、品質ギャップ分析用Agent Skills
- 複数エージェントで再利用するAgent Skillsと、安全な配布・同期スクリプト

## 適用方針

資料は初期値であり、導入先の文書構成、公開基盤、言語、リンク、ビルド、既存の課題・要求管理を調査したうえで選択適用します。小規模なCLIではREADMEと必要最小限の資料で十分なことがあり、大規模な製品では利用者・開発者・運用者ごとの案内や公開リファレンスが必要なことがあります。DevConcord固有のディレクトリ構成、README形式、品質評価軸を一律に強制しません。

## ライセンス

個別に異なるライセンスが明記されていない限り、このリポジトリの資料・テンプレート・Agent SkillsはMITまたはApache License 2.0のいずれかを選択して利用できます。詳細は[MIT License](LICENSE-MIT)と[Apache License 2.0](LICENSE-APACHE)を参照してください。
