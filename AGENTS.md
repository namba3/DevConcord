# DevConcord リポジトリ作業指示

- リポジトリの目的と入口は `README.md`、資料体系は `docs/README.md` と `prompts/README.md` を確認してください。
- DDD、TDD、DbC、Self-documenting Code、Doc Comments、Annotation Comments、Performance by Designなどの既存原則と、課題表を作業管理の正本とする運用を維持してください。
- 資料を変更するときは、関連するガイド、テンプレート、プロンプト、READMEの用語とリンクを確認し、必要な範囲だけを更新してください。
- 外部の導入先リポジトリを編集せず、このリポジトリの資料・検証コードだけを対象にしてください。
- 資料・検証コードを変更した場合は、`python3 scripts/validate_docs.py`、`python3 -B -m unittest discover -s tests -v`、`npx --yes markdownlint-cli2@0.23.3 "**/*.md"` を実行し、未実施の検証を成功として報告しないでください。
