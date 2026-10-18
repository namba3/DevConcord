# DevConcord リポジトリ作業指示

- リポジトリの目的と入口は `README.md`、資料体系は `docs/README.md` と `docs/agent-skills.md` を確認してください。
- DDD、SDD、TDD、DbC、Self-documenting Code、UX-Driven Functional Design、Performance / Robustness / Replaceability / Security by Design、Documentation by Designの基本原則を維持してください。各原則は変更に関係する範囲で適用し、UI/UXは利用者の目的・タスクから機能を導く人間中心設計の入力として扱います。Doc Comments・Annotation Commentsと、課題表を作業管理の正本とする運用も維持してください。
- 要求・設計では、必要に応じて利用者の目的/タスク、受け入れ条件、性能ワークロード、異常時の契約・状態整合性・回復方法、交換価値のある技術依存境界、資産・脅威・信頼境界・セキュリティ不変条件・検証を接続してください。脅威と変更影響に応じて分析範囲を選び、交換性のために全依存を抽象化せず、費用対効果を考慮します。
- 重要な設計判断や未解決リスクには、利用可能性を確認してDevConcord系専門Skills（`devconcord-design-*`、`devconcord-ux-functional-design`、`devconcord-documentation-architecture`等）の利用を検討してください。独立した検証設計には`devconcord-test-design`、複雑な変更の段階的計画には`devconcord-implementation-planning`も候補です。これらの原則と必要に応じたSkillsの案内は、変更リスクが低い場合やSkillの利用可否が未確認の場合もAGENTS.mdに簡潔に記載しますが、全原則の詳細分析やSkill実行を一律に要求しません。Project Scope / User Scopeを確認し、未導入・未確認のSkillを利用可能と断定しないでください。`devconcord-repository-review`と`devconcord-gap-analysis`は専門設計Skillsと異なる評価用Skillsです。他の提供元の有用なSkillsも排除せず、自動インストールや実行を前提にしません。
- 品質評価では既存の完成度10軸・重みを維持し、UI/UX・性能・堅牢性を関連する既存軸へ、交換可能性は主に設計・アーキテクチャとコード品質・保守性へ反映してください。新しい軸や課題・リスクの二重台帳は追加しません。
- 資料を変更するときは、関連するガイド、テンプレート、Skills、READMEの用語とリンクを確認し、必要な範囲だけを更新してください。
- コード・仕様・設定の変更では関連文書への影響を確認し、対象読者・正本・既存導線を保って必要な資料だけ更新してください。文書設計の詳細は[共通ガイド](docs/common/documentation-design.md)を参照し、大きな文書体系のレビュー・改善には利用可能なら `devconcord-documentation-architecture` Skillを使います。
- レビュー作業では [`REVIEW.md`](REVIEW.md) を先に読み、リポジトリ固有の確認観点を適用してください。
- 外部の導入先リポジトリを編集せず、このリポジトリの資料・検証コードだけを対象にしてください。
- 資料・検証コードを変更した場合は、`python3 scripts/validate_docs.py`、`python3 -B -m unittest discover -s tests -v`、`npx --yes markdownlint-cli2@0.23.3 "**/*.md"` を実行し、未実施の検証を成功として報告しないでください。
- Python検証器の依存は [`requirements-dev.txt`](requirements-dev.txt) に固定しています。必要な場合は [`docs/README.md`](docs/README.md) の手順で隔離環境へ導入してください。
- Agent Skillsの正本は `.agents/skills/` です。外部リポジトリへの配布・同期は [`scripts/manage_skills.py`](scripts/manage_skills.py) をdry-runして差分を確認し、適用時だけ `--apply` を指定してください。通常同期では同じGit履歴の前進と導入先ハッシュを検証し、出典変更は `rebind-source`、異常終了後の回復は `recover` の明示操作として扱います。
- Skillsを変更した場合は標準メタデータ、Skill内リンク、配布可能なファイル構成、agentごとの探索先・重複可能性を検証します。同名Skillは探索範囲を持つagentと内容一致/競合を区別し、Copilotが複数パスから発見し得る構成は実機未検証と報告してください。導入先のローカル編集や未知manifestを上書きせず、同名Skill追加を一律許可・禁止しません。
- 初回導入・同期の手順変更は [`tests/integration/README.md`](tests/integration/README.md) の受け入れシナリオに照らして確認し、実際のAIエージェント実行と文書ユニットテストの証拠を区別してください。
