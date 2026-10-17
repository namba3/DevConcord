# DevConcord リポジトリ作業指示

- リポジトリの目的と入口は `README.md`、資料体系は `docs/README.md` と `prompts/README.md` を確認してください。
- DDD、SDD、TDD、DbC、Self-documenting Code、Doc Comments、Annotation Comments、Performance by Design、Robustness by Design等の原則と、課題表を作業管理の正本とする運用を維持してください。UI/UXは機能要求を方向付ける人間中心設計の入力として扱います。
- 要求・設計では、必要に応じて利用者の目的/タスク、受け入れ条件、性能ワークロード、異常時の契約・状態整合性・回復方法を接続してください。製品形態とリスクに応じて適用し、根拠のない目標や過剰なプロセスを追加しないでください。
- 品質評価では既存の完成度10軸・重みを維持し、UI/UX・性能・堅牢性を関連する既存軸へ反映してください。新しい軸や課題・リスクの二重台帳は追加しません。
- 資料を変更するときは、関連するガイド、テンプレート、プロンプト、READMEの用語とリンクを確認し、必要な範囲だけを更新してください。
- レビュー作業では [`REVIEWS.md`](REVIEWS.md) を先に読み、リポジトリ固有の確認観点を適用してください。
- 外部の導入先リポジトリを編集せず、このリポジトリの資料・検証コードだけを対象にしてください。
- 資料・検証コードを変更した場合は、`python3 scripts/validate_docs.py`、`python3 -B -m unittest discover -s tests -v`、`npx --yes markdownlint-cli2@0.23.3 "**/*.md"` を実行し、未実施の検証を成功として報告しないでください。
- 初回導入・同期の手順変更は [`tests/integration/README.md`](tests/integration/README.md) の受け入れシナリオに照らして確認し、実際のAIエージェント実行と文書ユニットテストの証拠を区別してください。
