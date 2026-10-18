# DevConcord

DevConcordは、設計・開発・レビューの共通資料、テンプレート、Agent Skillsを提供します。Agent Skillsを作業ワークフローの正本とし、特定の技術スタックやエージェントを前提にせず、導入先の既存規約・規模・用途に合わせて必要な部分を選んで利用します。

## 目的から選ぶ

初回利用時は、先に[実行例付きの導入ガイド](docs/getting-started.md)を開いてください。Agent Skillsはユーザー単位のUser Scopeが標準で、プロジェクトへのコピーはチーム共有・CI等のProject Scopeが必要な場合に選びます。ワークフロー作業は導入先リポジトリを作業コンテキストにし、DevConcordは読み取り専用の参照元として扱います。

| 目的 | 入口 |
|---|---|
| 設計書から新規Bootstrapする | [Bootstrapの実行例](docs/getting-started.md#3-設計書から新規bootstrapするcodex-cli) |
| 既存リポジトリへAdoptionする | [Adoptionの実行例](docs/getting-started.md#4-既存リポジトリへadoptionするcodex-cli) |
| はじめてDevConcordを使う | [導入と運用ガイド](docs/getting-started.md) |
| 設計書から新しいプロジェクトを始める | [`devconcord-bootstrap-from-design` Skill](.agents/skills/devconcord-bootstrap-from-design/SKILL.md) |
| 既存プロジェクトへ規約を選んで導入する | [`devconcord-adopt-guidance` Skill](.agents/skills/devconcord-adopt-guidance/SKILL.md) |
| 実装前に変更の影響範囲を評価する | [`devconcord-repository-review` Skill](.agents/skills/devconcord-repository-review/SKILL.md)のChange Impact Assessment |
| 要求・契約から独立したテスト戦略を設計する | [`devconcord-test-design` Skill](.agents/skills/devconcord-test-design/SKILL.md) |
| 複雑な変更を検証可能な実装単位へ分ける | [`devconcord-implementation-planning` Skill](.agents/skills/devconcord-implementation-planning/SKILL.md) |
| DevConcord原則との品質ギャップを全体/差分診断する | [`devconcord-gap-analysis` Skill](.agents/skills/devconcord-gap-analysis/SKILL.md) |
| 導入済みの共通資料を更新する | [資料Synchronizationの実行例](docs/getting-started.md#8-共通ガイドのsynchronization) |
| 共通原則・テンプレートを探す | [資料一覧](docs/README.md) |
| 資産・脅威・信頼境界からセキュリティ設計する | [`devconcord-design-security` Skill](.agents/skills/devconcord-design-security/SKILL.md)と[Security by Design](docs/common/ai-assisted-development.md#97-security-by-design) |
| Agent Skillsを選ぶ | [Skills一覧](docs/agent-skills.md#skills) |
| ローカルDevConcord資料を版固定で参照する | [`devconcord-reference` Skill](.agents/skills/devconcord-reference/SKILL.md)と[参照運用](docs/agent-skills.md#ローカルdevconcord資料の参照) |
| Skill非対応環境で手動利用する | [Skill本体と参照資料を渡す方法](docs/agent-skills.md#skills非対応環境で手動利用) |
| User ScopeのSkillsを導入・同期・検証する | [Getting Started](docs/getting-started.md#2-agent-skillsをユーザー単位でインストールする)または[Skills運用ガイド](docs/agent-skills.md) |
| Project ScopeのSkillsを導入する | [Project Scopeの実行例](docs/getting-started.md#7-project-scopeでskillsを導入する任意) |
| ドキュメント体系を設計・改善する | [ドキュメント設計ガイド](docs/common/documentation-design.md) |

## 収録内容

- DDD、Self-documenting Code、SDD、DbC、TDD、Performance / Robustness / Replaceability / Security by Design等の開発・設計ガイド
- 要求仕様、ADR、課題管理、リスク管理、完成度評価の規約とテンプレート
- READMEを含む文書設計、導入、更新、検証のための共通指針
- `AGENTS.md`・`REVIEW.md`生成、Bootstrap、Adoption、影響評価、テスト設計、実装計画、Synchronization、品質ギャップ分析用Agent Skills
- 複数エージェントで再利用するAgent Skillsと、安全な配布・同期スクリプト

## 適用方針

資料は初期値であり、導入先の文書構成、公開基盤、言語、リンク、ビルド、既存の課題・要求管理を調査したうえで選択適用します。小規模なCLIではREADMEと必要最小限の資料で十分なことがあり、大規模な製品では利用者・開発者・運用者ごとの案内や公開リファレンスが必要なことがあります。DevConcord固有のディレクトリ構成、README形式、品質評価軸を一律に強制しません。

## ライセンス

個別に異なるライセンスが明記されていない限り、このリポジトリの資料・テンプレート・Agent SkillsはMITまたはApache License 2.0のいずれかを選択して利用できます。詳細は[MIT License](LICENSE-MIT)と[Apache License 2.0](LICENSE-APACHE)を参照してください。
