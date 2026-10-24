# 資料・テンプレート一覧

このディレクトリには、複数のソフトウェア開発プロジェクトで再利用する運用ガイドと文書テンプレートを置きます。プロジェクト固有の仕様・設計・運用記録は、それぞれの対象リポジトリへ配置してください。

初回利用では[実行例付きの導入ガイド](getting-started.md)からUser ScopeのSkillsセットアップ、Bootstrap、Adoptionの該当シナリオを選んでください。Agent Skillsはユーザー単位が標準で、Project Scopeはチーム共有・CI等に使う任意の方式です。ワークフロー作業は導入先を作業コンテキストとし、DevConcordを参照元として使います。Skillsの出典管理・復旧などの詳細は[Agent Skills運用ガイド](agent-skills.md)が正本です。

作業別の再利用可能なAgent Skillsの正本はリポジトリルートの [`.agents/skills/`](../.agents/skills/) にあります。[`devconcord-reference`](../.agents/skills/devconcord-reference/SKILL.md)は共通資料を読むためのAI向け窓口、[`manage_skills.py reference`](../scripts/manage_skills.py)は出典・版・パスを検証して内容を返す決定的なCLIです。各業務Skillが必要な資料パスを決め、共通Skillが使えない場合も同じCLIを直接実行できます。Skillsの選択は[Agent Skills運用ガイドの一覧](agent-skills.md#skills)、Scopeや参照の詳細は[運用手順](agent-skills.md#ローカルdevconcord資料の参照)を参照してください。Skills非対応環境では、該当する `SKILL.md` と必要な `references/` の全文を対象エージェントへ渡します。

## 共通

| 資料 | 用途 |
|---|---|
| [AI支援開発ガイド](common/ai-assisted-development.md) | DDD・自己説明性・Performance / Robustness / Replaceability / Security / Observability by Design、契約・検証、Doc Comments・Annotation Comments、プライバシー・環境衛生 |
| [ドキュメント設計ガイド](common/documentation-design.md) | 読者中心の情報設計、README・文書の役割、ナビゲーション、Single Source of Truth、変更影響、Docs as Code |
| [Agent Skills運用ガイド](agent-skills.md) | 導入先へのSkillsの選択導入、共用、更新、manifest、復旧、検証 |
| [`devconcord-reference` Skill](../.agents/skills/devconcord-reference/SKILL.md) | ローカル共通資料を要求元Skillの版に合わせて参照する |
| [`devconcord-design-orchestration` Skill](../.agents/skills/devconcord-design-orchestration/SKILL.md) | 委任された範囲で、要求・設計・判断・検証を段階的に具体化・改善し、整合させる |
| [`devconcord-development-orchestration` Skill](../.agents/skills/devconcord-development-orchestration/SKILL.md) | 既存設計と課題表に基づく複数の開発反復を、検証・レビュー・品質ゲートで制御する |

## アプリ設計

| 資料 | 用途 |
|---|---|
| [UI/UX設計ガイド](application-design/ui-ux-guide.md) | Web・デスクトップを中心としたUI/UX設計、AI可読なモックアップ、検証 |
| [UI/UX設計クイックチェック](application-design/ui-ux-quick-reference.md) | 設計レビューや実装前後に使う短い確認項目 |
| [Secrets by Design](application-design/secrets-by-design.md) | 長期秘密の削減、ID連携、資格情報のライフサイクルと検証 |
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

## 目的から探す

| 読者の目的 | まず読む資料 |
|---|---|
| 設計原則とAI支援開発の共通ルールを理解する | [AI支援開発ガイド](common/ai-assisted-development.md)、[AI開発クイックリファレンス](common/ai-development-quick-reference.md) |
| 要求仕様や設計判断を記録する | [要求仕様テンプレート](application-design/templates/requirements.md)、[ADRテンプレート](application-design/templates/adr.md) |
| 複数の設計領域をまたいで設計を進める・改善する | [`devconcord-design-orchestration` Skill](../.agents/skills/devconcord-design-orchestration/SKILL.md) |
| 利用者タスクから機能・状態・UIモックアップを設計する | [UI/UX設計ガイド](application-design/ui-ux-guide.md)、[UI/UXクイックチェック](application-design/ui-ux-quick-reference.md)、[`devconcord-ux-functional-design` Skill](../.agents/skills/devconcord-ux-functional-design/SKILL.md) |
| 性能・堅牢性・依存境界・セキュリティを検討する | [設計原則](common/ai-assisted-development.md)、[Secrets by Design](application-design/secrets-by-design.md)と個別の `devconcord-design-performance`、`devconcord-design-robustness`、`devconcord-design-replaceability`、`devconcord-design-security` [Skills](agent-skills.md#skills) |
| 可観測性・診断可能性を設計する | [AI支援開発ガイド §9.5](common/ai-assisted-development.md#95-robustness-by-design)、[`devconcord-observability-design` Skill](../.agents/skills/devconcord-observability-design/SKILL.md) |
| READMEや文書体系を改善する | [ドキュメント設計ガイド](common/documentation-design.md)、[`devconcord-documentation-architecture` Skill](../.agents/skills/devconcord-documentation-architecture/SKILL.md) |
| DevConcord原則との品質ギャップを全体/差分診断する | [`devconcord-gap-analysis` Skill](../.agents/skills/devconcord-gap-analysis/SKILL.md) |
| 提案された変更の実装前影響を評価する | [`devconcord-repository-review` Skill](../.agents/skills/devconcord-repository-review/SKILL.md)のChange Impact Assessment |
| 要求・契約から独立したテストを設計する | [`devconcord-test-design` Skill](../.agents/skills/devconcord-test-design/SKILL.md) |
| 複雑な変更を検証可能な実装単位へ計画する | [`devconcord-implementation-planning` Skill](../.agents/skills/devconcord-implementation-planning/SKILL.md) |
| 既存課題表から実装対象を選び、検証・状態更新する | [`devconcord-issue-driven-development` Skill](../.agents/skills/devconcord-issue-driven-development/SKILL.md) |
| 複数の実装単位を反復し、品質を再評価して続行・停止する | [`devconcord-development-orchestration` Skill](../.agents/skills/devconcord-development-orchestration/SKILL.md) |
| 課題・リスク・完成度を管理する | [課題管理・完成度評価規約](work-management/issue-tracking.md)、[リスク管理規約](work-management/risk-management.md) |
| レビュー基準を作る・調べる | [`devconcord-generate-agent-guidance` Skill](../.agents/skills/devconcord-generate-agent-guidance/SKILL.md)、[レビュー指針](../REVIEW.md) |
| 設計書から新規リポジトリを始める | [Bootstrapの実行例](getting-started.md#3-設計書から新規bootstrapするcodex-cli)、[`devconcord-bootstrap-from-design` Skill](../.agents/skills/devconcord-bootstrap-from-design/SKILL.md) |
| 既存プロジェクトへ規約を導入する | [Adoptionの実行例](getting-started.md#4-既存リポジトリへadoptionするcodex-cli)、[`devconcord-adopt-guidance` Skill](../.agents/skills/devconcord-adopt-guidance/SKILL.md) |
| 導入済み共通資料を更新する | [資料Synchronizationの実行例](getting-started.md#8-共通ガイドのsynchronization)、[`devconcord-sync-guidance` Skill](../.agents/skills/devconcord-sync-guidance/SKILL.md) |
| User ScopeのSkillsを導入・更新・検証する | [Skillsの実行例](getting-started.md#2-agent-skillsをユーザー単位でインストールする)、[Agent Skills運用ガイド](agent-skills.md) |
| Project Scopeを使ってSkillを共有する | [Project Scopeの実行例](getting-started.md#7-project-scopeでskillsを導入する任意)、[Agent Skills運用ガイド](agent-skills.md) |

## 選択と適用

これらの資料は適用先に合わせて選びます。README、公開サイト、ディレクトリ構造、既存規約を調査し、必要な部分だけを導入してください。Bootstrapは設計書から新規構成を作る手順、Adoptionは既存成果物を保護した初回導入、資料Synchronizationは導入済み共通資料の差分更新です。変更提案の実装前影響評価、テスト設計、実装計画もそれぞれ目的に応じた任意の作業です。Bootstrap / Adoption後の専門Skill推奨は、確認済みの設計状況や未解決事項に基づき一律実行しません。これらのSkillワークフローと、`manage_skills.py sync` によるAgent Skillsパッケージの同期は別操作です。具体的な作業場所・コマンド・検証は[はじめての導入と運用](getting-started.md)、Skillsの詳細契約は[Agent Skills運用ガイド](agent-skills.md)を参照してください。

要求IDからADR・実装・検証・課題への参照は変更リスクに応じて設けます。設計書の出典と共通資料の `guidance-provenance.md` を区別し、未確認事項を確定仕様にしません。課題表を作業管理の正本とし、リスク対応作業の別台帳は追加しません。完成度は既存10軸で評価し、SDSは独立した補助指標として総合完成度へ加算しません。新しい品質評価軸は追加しません。

文書品質の詳しい原則は[ドキュメント設計ガイド](common/documentation-design.md)、Skillsの安全な配置・重複・出典・復旧は[Agent Skills運用ガイド](agent-skills.md)、個別設計原則はリンク先のガイド・Skillを正本として参照してください。資料やテンプレートを一部だけ導入する場合は、相対リンクを対象リポジトリ内で解決できる配置へ合わせます。

## 自動検証

Pull Request と `main` への push で、Markdownlint、DevConcord内のMarkdown/HTMLリンク、Agent Skillsのfrontmatter・配置・相対リンク・探索先間の名前重複、管理規約・テンプレートの既知の必須項目と正規評価軸/重み、課題・ADR・リスク・要求状態の定義間整合、Markdown中の個人情報・個人環境情報・秘密らしき値のヒューリスティック検査を行います。Python検証はUbuntu/Python 3.12、Ubuntu/Python 3.14、Windows/Python 3.14で実行し、MarkdownlintはNode.js 22で別ジョブとして1回実行します。任意形式の課題表の全ID・状態・優先度、実際の要求仕様/ADR、DevConcord資料を導入した外部リポジトリ、AIエージェントが規約に従ったかは検証しません。Markdown上の規約検査は正規資料・テンプレートの静的な整合確認であり、実プロジェクトの適合や設計判断の品質を保証しません。プライバシー検査はMarkdown中の候補検出に限られ、誤検出・見逃しがあるため、ソース/設定を含む専用シークレットスキャナーの代わりにはなりません。導入・同期ヘルパーの決定的なテストと、実AIエージェントを使う手動評価は[統合シナリオ](../tests/integration/README.md)で分離しています。Workflowはブランチ保護/rulesetを設定しないため、管理者はGitHub上で `main` へのマージに必要なチェックを設定してください。ローカルでは仮想環境にPython依存を一度インストールしてから次を実行できます。

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements-dev.txt
python3 scripts/validate_docs.py
python3 -B -m unittest discover -s tests -v
npx --yes markdownlint-cli2@0.23.3 "**/*.md"
```

資料中のコード片には説明用・疑似コードも含むため、すべてのコードフェンスを実行可能なサンプルとは扱いません。実行可能なサンプルを追加する場合は、対象を特定した検証を別途設けます。
