# 資料・テンプレート一覧

このディレクトリには、複数のソフトウェア開発プロジェクトで再利用する運用ガイドと文書テンプレートを置きます。プロジェクト固有の仕様・設計・運用記録は、それぞれの対象リポジトリへ配置してください。

初回導入・更新適用の手順は[はじめての導入と運用](getting-started.md)を参照してください。

## 共通

| 資料 | 用途 |
|---|---|
| [AI支援開発ガイド](common/ai-assisted-development.md) | DDD・自己説明性・Doc Comments・Annotation Comments・性能設計の原則と、プライバシー・環境衛生を含む開発手法 |

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
- プライバシー・環境衛生とPerformance by Designは共通開発原則として扱い、既存の完成度10評価軸へ反映します。絶対パスや性能計測を一律禁止・強制するのではなく、必要性と対象環境に応じて適用します。
- 要求と受け入れ条件は要求仕様書で管理し、要求IDからADR・実装・検証・課題を必要な範囲で参照します。将来の不確実性を管理する場合はリスク規約を使い、対応作業は課題表に置きます。
- 課題表と規約のリンクを保つ場合は `work-management/` をディレクトリごと対象リポジトリの `docs/` へコピーします。テンプレートだけをコピーする場合は、規約へのリンク先を対象内の配置に合わせて変更します。
- AIエージェントに常時適用する作業ルールは対象リポジトリの `AGENTS.md`、レビュー専用の観点は `REVIEWS.md` に置くための[生成プロンプト](../prompts/README.md)も用意しています。
- 既存プロジェクトへ導入するときは、[導入プロンプト](../prompts/adopt-guidance.md)で既存規約との重複・差異を確認してから適用します。
- 導入済み資料を更新するときは、[更新プロンプト](../prompts/sync-guidance.md)で資料ごとの比較基準コミット以降の差分と、適用メモに残る保留項目を確認します。
- AIへ詳細ガイドを渡す際は、全文ではなく必要な節を指定してください。[AI開発クイックリファレンス](common/ai-development-quick-reference.md)と[UI/UXクイックチェック](application-design/ui-ux-quick-reference.md)から関連する詳細節を選べます。

## 自動検証

Pull Request と `main` への push で、Markdownlint、内部リンク、課題表テンプレートの必須項目、課題ID・優先度・状態の表記、SDSと総合完成度の軸・重み、Markdown中の個人情報・個人環境情報・秘密らしき値のヒューリスティック検査を行います。プライバシー検査は候補の検出であり、誤検出・見逃しがあるため専用シークレットスキャナーの代わりにはなりません。ローカルでは次を実行できます。

```sh
python3 scripts/validate_docs.py
python3 -B -m unittest discover -s tests -v
npx --yes markdownlint-cli2@0.23.3 "**/*.md"
```

資料中のコード片には説明用・疑似コードも含むため、すべてのコードフェンスを実行可能なサンプルとは扱いません。実行可能なサンプルを追加する場合は、対象を特定した検証を別途設けます。
