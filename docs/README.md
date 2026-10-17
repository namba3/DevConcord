# 資料・テンプレート一覧

このディレクトリには、複数のソフトウェア開発プロジェクトで再利用する運用ガイドと文書テンプレートを置きます。プロジェクト固有の仕様・設計・運用記録は、それぞれの対象リポジトリへ配置してください。

初回導入・更新適用の手順は[はじめての導入と運用](getting-started.md)を参照してください。

## 共通

| 資料 | 用途 |
|---|---|
| [AI支援開発ガイド](common/ai-assisted-development.md) | DDD・自己説明性・Performance / Robustness / Replaceability by Design、契約・検証、Doc Comments・Annotation Comments、プライバシー・環境衛生 |

## アプリ設計

| 資料 | 用途 |
|---|---|
| [UI/UX設計ガイド](application-design/ui-ux-guide.md) | Web・デスクトップを中心としたUI/UX設計・検証 |
| [UI/UX設計クイックチェック](application-design/ui-ux-quick-reference.md) | 設計レビューや実装前後に使う短い確認項目 |
| [要求仕様テンプレート](application-design/templates/requirements.md) | 機能・非機能要求と検証可能な受け入れ条件の記録 |
| [設計判断記録（ADR）テンプレート](application-design/templates/adr.md) | 重要な設計判断、代替案、影響の記録 |

## 作業管理

| 資料 | 用途 |
|---|---|
| [課題管理・完成度評価規約](work-management/issue-tracking.md) | 課題表の記録、更新、評価と運用チェック |
| [リスク管理規約](work-management/risk-management.md) | 将来の不確実性・残余リスクの記録。対応作業は課題表で管理 |
| [プロジェクト概要テンプレート](work-management/templates/project-overview.md) | 目的、範囲、関係者、制約、成功条件の共有 |
| [課題一覧テンプレート](work-management/templates/issue-register.md) | 課題の優先度、状態、完了条件、根拠の管理 |
| [リリースチェックリスト](work-management/templates/release-checklist.md) | リリース前の検証、配布、周知、ロールバック確認 |

## 選び方

- 新規プロジェクトでは、まず[プロジェクト概要テンプレート](work-management/templates/project-overview.md)を埋め、必要な文書だけを選びます。
- 要求や設計判断を追跡する場合は、アプリ設計の要求仕様やADRを追加します。
- 課題一覧の評価基準や更新手順は[課題管理・完成度評価規約](work-management/issue-tracking.md)を参照します。
- コードの自己説明性とSDSの基準は、AI支援開発ガイドと課題管理規約にあります。SDSは独立した補助指標で、既存の総合完成度へ加算しません。
- Doc CommentsとAnnotation Commentsの記法・対象・課題表との連携は、[AI支援開発ガイド §2.2](common/ai-assisted-development.md#22-doc-commentsとannotation-comments)を参照してください。コメント数を品質指標にはしません。
- UI/UXは利用者の目的、タスク、操作、状態、回復条件を導き、機能要求と検証へつなぐ設計入力です。Web・デスクトップ・CLI・ライブラリ等の製品形態に合わせ、GUI固有要件を一律強制しません。
- DDD・Self-documenting Code・Performance by Design・Robustness by Design・Replaceability by Designは横断的な設計原則として扱います。Performance / Robustnessとプライバシー・環境衛生は既存の完成度10評価軸へ反映し、新しい評価軸は追加しません。絶対パス、性能計測、故障注入を一律禁止・強制せず、必要性・影響・対象環境に応じて適用します。
- Robustness by Designは、重要な異常条件・データ整合性・原子性・再実行・復旧・診断を初期設計へ含める考え方です。対応作業は既存課題表で管理し、別の作業台帳を作りません。
- Replaceability by Designは、変更価値のある技術依存だけを費用対効果に基づいて境界化します。全依存の抽象化や無変更の交換を要求せず、主に既存の設計・アーキテクチャ、コード品質・保守性の評価根拠として扱います。
- 要求と受け入れ条件は要求仕様書で管理し、要求IDからADR・実装・検証・課題を必要な範囲で参照します。将来の不確実性を管理する場合はリスク規約を使い、対応作業は課題表に置きます。
- 課題表と規約のリンクを保つ場合は `work-management/` をディレクトリごと対象リポジトリの `docs/` へコピーします。テンプレートだけをコピーする場合は、規約へのリンク先を対象内の配置に合わせて変更します。
- AIエージェントに常時適用する作業ルールは対象リポジトリの `AGENTS.md`、レビュー専用の観点は `REVIEWS.md` に置くための[生成プロンプト](../prompts/README.md)も用意しています。
- 既存プロジェクトへ導入するときは、[導入プロンプト](../prompts/adopt-guidance.md)で既存規約との重複・差異を確認してから適用します。
- 導入済み資料を更新するときは、[更新プロンプト](../prompts/sync-guidance.md)で資料ごとの比較基準コミット以降の差分と、適用メモに残る保留項目を確認します。
- AIへ詳細ガイドを渡す際は、全文ではなく必要な節を指定してください。[AI開発クイックリファレンス](common/ai-development-quick-reference.md)と[UI/UXクイックチェック](application-design/ui-ux-quick-reference.md)から関連する詳細節を選べます。

## 自動検証

Pull Request と `main` への push で、Markdownlint、DevConcord内のMarkdown/HTMLリンク、管理規約・テンプレートの既知の必須項目と正規評価軸/重み、課題・ADR・リスク・要求状態の定義間整合、Markdown中の個人情報・個人環境情報・秘密らしき値のヒューリスティック検査を行います。任意形式の課題表の全ID・状態・優先度、実際の要求仕様/ADR、DevConcord資料を導入した外部リポジトリ、AIエージェントが規約に従ったかは検証しません。Markdown上の規約検査は正規資料・テンプレートの静的な整合確認であり、実プロジェクトの適合や設計判断の品質を保証しません。プライバシー検査はMarkdown中の候補検出に限られ、誤検出・見逃しがあるため、ソース/設定を含む専用シークレットスキャナーの代わりにはなりません。導入・同期ヘルパーの決定的なテストと、実AIエージェントを使う手動評価は[統合シナリオ](../tests/integration/README.md)で分離しています。CIはPython 3.14、Node.js 22、markdownlint-cli2 0.23.3およびrequirements-dev.txtで固定したPython依存を使います。Workflowはブランチ保護/rulesetを設定しないため、管理者はGitHub上で `main` へのマージにDocumentationワークフローの必須チェックを設定してください。ローカルでは仮想環境にPython依存を一度インストールしてから次を実行できます。

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_docs.py
python3 -B -m unittest discover -s tests -v
npx --yes markdownlint-cli2@0.23.3 "**/*.md"
```

資料中のコード片には説明用・疑似コードも含むため、すべてのコードフェンスを実行可能なサンプルとは扱いません。実行可能なサンプルを追加する場合は、対象を特定した検証を別途設けます。
