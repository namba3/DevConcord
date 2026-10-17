# ソフトウェア開発プロジェクト運用資料

このリポジトリは、ソフトウェア開発プロジェクトの計画・設計・実装・レビュー・リリースを運用するための共通資料、テンプレート、AI向けプロンプトを管理します。

## ディレクトリ

- [`docs/`](docs/README.md): 共通設計原則・開発/レビュー規約、要求・リスク・課題表管理、完成度評価と各種テンプレート
- [`prompts/`](prompts/README.md): `AGENTS.md`・`REVIEWS.md` の生成、設計書からの新規リポジトリ初期化、既存プロジェクトへの初回導入、導入済み資料の差分同期に使うプロンプト
- [`.agents/skills/`](.agents/skills/): 複数エージェントで再利用するAgent Skillsの正本。配布・同期は [`scripts/manage_skills.py`](scripts/manage_skills.py) で安全に行う

## 使い方

導入手順、Codex CLI・VS Codeでの使い方、導入後チェック、資料版の記録方法は[はじめての導入と運用](docs/getting-started.md)を参照してください。

ガイドとテンプレートは[資料一覧](docs/README.md)、初回導入・更新や指示ファイル生成に使うプロンプトは[プロンプト一覧](prompts/README.md)から選べます。

共通資料には、DDD・Self-documenting Code・Performance by Design・Robustness by Design・Replaceability by Designの横断原則、SDD・DbC・TDD等の実践手法、開発・レビュー・品質管理の規約があります。UI/UXは見た目だけでなく、人間中心の要求・機能設計を方向付ける入力として扱います。要求仕様とリスクを追跡し、課題表方式の作業管理、SDS、既存10軸の完成度評価を支援します。資料の一覧と選び方は[docs/README.md](docs/README.md)を参照してください。

資料は初期値です。設計書から新規リポジトリを初期化する場合は `bootstrap-from-design.md`、既存リポジトリへ共通規約を導入する場合は `adopt-guidance.md`、導入済み資料を更新する場合は `sync-guidance.md` を使い分けます。対象プロジェクトに既存のルールや管理方法がある場合は、それを確認してから適用してください。プロンプトの選択や手順は[prompts/README.md](prompts/README.md)と[導入ガイド](docs/getting-started.md)を参照してください。

作業単位で再利用できるAgent Skillsも提供します。正本は `.agents/skills/` にあり、CodexとCopilotの標準探索先で使えます。Claude CodeではSkillを `.claude/skills/` へ選択的にインストールします。外部リポジトリへのインストール・同期はまずdry-runで差分を確認し、明示的に `--apply` を付けます。詳細、同名Skillの重複回避、既存プロンプトとの使い分けは[導入ガイド](docs/getting-started.md)を参照してください。

共通開発原則では、DDDで概念と責務の正しさを、Self-documenting Codeで理解可能性を、Performance by Designで処理構造の効率性を、Robustness by Designで異常時の耐性・整合性・回復可能性を、Replaceability by Designで必要な技術依存の局所化と変更容易性を重視します。UI/UXは利用者の目的から必要な機能・操作・状態を導く人間中心の設計入力です。交換可能性は必要な境界に限り、正確性・セキュリティ・アクセシビリティ等も重要な品質として保ちます。要求への適合、性能、失敗時保証、技術境界の契約は必要な受け入れ条件と独立検証で確かめます。詳しくは[資料一覧](docs/README.md)から各ガイドと課題管理規約を参照してください。

## ライセンス

個別に異なるライセンスが明記されていない限り、このリポジトリの資料・テンプレート・プロンプトはMITまたはApache License 2.0のいずれかを選択して利用できます。詳細は[MIT License](LICENSE-MIT)と[Apache License 2.0](LICENSE-APACHE)を参照してください。
