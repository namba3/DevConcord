# AI支援開発クイックリファレンス

日常の変更で使う最小手順です。各項目の詳しい背景や例は[AI支援開発ガイド](ai-assisted-development.md)の該当節を参照してください。すべての手法・成果物を全プロジェクトに強制するものではありません。

日常の依頼では内部workflow名を覚える必要はありません。目的、対象、委任範囲、変更してはいけない条件を指定します。AIは対象リポジトリの指示と現状から必要なworkflow・資料・検証を選び、権限や重要な判断が変わる場合にだけ確認します。

```text
課題表から次の重要課題を一つ選んで進めてください。
承認済みの範囲で実装・検証し、必要な正本だけを更新してください。
失敗・未実施の検証、ブロッカー、承認が必要な判断を優先して報告してください。
```

## 開発の流れ

```text
人間: 目的・対象・委任範囲・制約を指定
           ↓
AI: 対象の指示・正本・現状から必要なworkflowと検証を選択
           ↓
実装・検証 → 関係する正本だけを更新 → 結果と例外を報告
```

## 検証選択

変更した面とリスクから必要な既存検証を選びます。すべての変更で全コマンドを実行する必要はありません。CIの回帰検査はローカルの選択実行にかかわらず維持します。

| 変更面 | 検証の入口 |
|---|---|
| Markdown・リンク・テンプレート | `python3 scripts/validate_docs.py` と `npx --yes markdownlint-cli2@0.23.3 "**/*.md"` |
| Skillのfrontmatter・内部ルーティング・参照 | `python3 scripts/manage_skills.py validate` と `python3 -B -m unittest discover -s tests -p 'test_agent_skills.py' -v` |
| Skill管理CLI・manifest・移行・復旧 | `python3 -B -m unittest discover -s tests -p 'test_manage_skills.py' -v` と操作別の失敗・復旧テスト |
| Issue・DEC・ADR・Risk・HANDOFF規約 | `python3 -B -m unittest discover -s tests -p 'test_agent_skills.py' -v` と該当する統合fixture |
| 複数領域にまたがる変更、または回帰範囲が不明 | `python3 -B -m unittest discover -s tests -v` と必要な追加検証 |

コマンドはリポジトリの依存関係・CI・既存手順に合わせます。未実施の検証は成功として扱わず、ホスト実機・リモートCI・実エージェントの証拠とローカル静的検査を区別します。

検証結果にコンパイラ・linter・静的解析の警告があれば、件数だけでなく影響と変更前の基準を確認します。新規警告は原則同じ変更内で解消し、関連する既存警告は安全性と費用対効果に応じて改善します。安易な抑制やCIの弱体化を避け、詳細は[Warning Hygiene & Progressive Remediation](ai-assisted-development.md#105-warning-hygiene-progressive-remediation)に従います。

## 作業開始前

- 既存の `AGENTS.md`、仕様、ADR、課題一覧、関連コードとテストを確認する。
- 変更の目的、範囲、対象外、互換性への影響を特定する。
- 変更規模とリスクに応じ、利用者の目的/タスク、依存関係・公開API・データ・状態・異常時の保証/回復・セキュリティ境界・対象環境・関連資料への影響を確認する。局所的な変更は限定的と判断した根拠を短く残す。
- 曖昧さや不足情報は事実のように補わず、仮定・未確認事項として示す。
- 専門Skillと検証の深さは、影響・不確実性・波及範囲・可逆性・証拠に比例させる。全Skillや全手法を一律適用せず、未知を低リスクとみなさない。途中でリスクが変わったら見直す（[Risk-Proportional原則](ai-assisted-development.md#175-リスク比例型skill適用と検証)）。
- 振る舞いを変える作業では、観測可能な受け入れ条件と検証方法を定める。
- 実装前の具体的な影響評価、独立した期待値に基づくテスト設計、複雑な作業の段階化が必要な場合は、それぞれ対応する任意のSkillを選ぶ。軽微な変更へ一律に適用せず、提案・実装・実行・合格を区別する。
- 要望・アイデアは既存課題との重複と追跡価値を確認して必要な場合だけISSへ記録する。採否は作業状態と分け、提案の存在や採用だけで実装を開始しない（[課題管理規約 §4.14](../work-management/issue-tracking.md#414-要望提案アイデア)）。
- 原因不明の重要障害、実在する互換性リスク、明示的なリリース作業、依存の変更/重大リスク、エージェントSkillの実効性評価では対応する専門Skillを必要な場合だけ検討する。通常開発の必須工程ではなく、未利用を欠陥としない。詳細は[AI支援開発ガイド §17.3–17.5](ai-assisted-development.md#175-リスク比例型skill適用と検証)を参照する。

## 設計・実装

- 意味・責務・契約・振る舞いをコードの名前、型、API、構造、テストで表現できるか考える。自己説明性はコメントを減らすことではなく、コードで伝わらない理由・制約をコメントや設計資料で補うこと。
- DDDで概念と責務を、Self-documenting Codeで理解可能性を、Performance by Designで処理構造の効率性を、Robustness by Designで異常条件・整合性・回復可能性を、Replaceability by Designで必要な技術依存境界を、Security by Designで資産・脅威・信頼境界に応じた制御と検証を、Observability & Diagnosability by Designで必要十分かつ安全な診断証拠を考える。資格情報を扱う場合は、長期秘密が必要か、主体ID・権限・ライフサイクルをどう制御するかを検討する（[Secrets by Design](../application-design/secrets-by-design.md)）。UI/UXは利用者の要求と機能設計を方向付ける入力とする。DbC・テスト・計測で契約と品質を確かめる。
- ドメイン用語と既存の責務境界を保ち、必要な箇所だけ抽象化する。
- 交換可能性は将来変更の可能性・影響と抽象化の費用対効果で境界を選ぶ。単一実装で十分なら具体型を使い、ライブラリAPIの一対一ラッパーや未使用の抽象を増やさない。
- UI/バックエンド固有型、状態、エラーが必要な境界を越えてコアへ漏れないか、交換後のデータ移行・意味的契約・性能・セキュリティ・UX影響を確認する。完全無変更の交換を前提にしない。
- 機能要求は必要に応じてユーザー目標、主要タスク、操作・状態・フィードバック、受け入れ条件と検証へ結ぶ。UIのない製品にはGUI固有要件を課さない。
- UX由来の要求では、必要に応じてTASK IDとREQ IDを相互参照し、要求から設計・検証へたどれるようにする。一対多/多対一はID参照で表し、独立したマトリクスを一律追加しない。
- 重要な契約は事前条件、事後条件、不変条件、失敗時の保証に分け、必要に応じて原子性、キャンセル時点、再実行時の副作用、回復方法を明記する。
- 性能上重要な経路はワークロード、データ規模、対象環境、測定方法と許容範囲から設計する。異常条件・部分成功・競合・資源不足等は影響に応じて選び、無条件の再試行・多重化を避ける。
- 公開・重要APIには利用者に必要なDoc Commentsを付け、契約・エラー・副作用・制約を実装と同期する。必要な場合だけ標準形式で使用例や性能特性を記載する。
- 未解決事項・暫定対応・重要な注意は `TODO`、`FIXME`、`HACK`、`NOTE`、`PERF`、`SECURITY`、`DEPRECATED` で明示する。重要な作業は既存の課題IDへ結び付け、進捗・完了条件は課題表で管理する。
- 課題の解決時に関連コメントを削除または有効な説明へ更新する。コメントの数を品質指標にせず、コード・コメント・資料・テストの整合を保つ。
- 重要で長く影響する設計判断はADRへ理由・代替案・影響とともに記録する。
- 変更は小さく保ち、仕様・テストを実装に都合よく弱めない。

## 検証・レビュー

- 受け入れ条件をテストや具体的な確認手順へ結び付ける。
- 守るべき設計制約を自動検査・テスト・人間のレビューのうち適した方法で確認する。
- 実施した検証、未実施の検証、環境上の制約を区別して報告する。
- 証跡がある場合は対象コミット、実行内容、環境、日時、結果を追跡できるようにする。過去の成功を変更後の保証に流用しない。
- 変更内容に応じて、個人・秘密・環境情報がコード、設定、ログ、文書、AIの報告に不要に含まれていないか確かめる。性能上重要な変更は想定ワークロードと計測根拠を扱い、実測なしの最適化を避ける。重要な失敗時保証は対応するテストで検証し、未確認範囲を示す。
- テスト成功だけで要求の正しさを証明したことにしない。仕様と期待値も確認する。
- コードレビュー前に対象リポジトリの `REVIEW.md` を読む（存在しない場合は明記する）。

## 記録の更新

- 課題IDは `ISS-0001` 形式、優先度は `P0`〜`P3`、状態は課題管理規約の列挙値を使う。
- 課題を完了にする前に完了条件と根拠を記録する。
- 共通DoDを該当する範囲で満たし、課題固有の完了条件も確認する。未実施の検証は理由と残余リスクを示す。
- 設計・要求・運用に影響する変更は、対応する資料も更新する。
- 要求は要求仕様書、設計判断はADR、作業と技術的負債は既存課題表、将来の不確実性はリスク記録を管理元とする。対応関係はID・リンクで結ぶ。
- 依存課題がある場合は依存先を確認し、ブロック状態と課題IDを使う。固定WIP数や別の進捗台帳は設けない。
- 重要な設計変更、リスク顕在化、リリース判断などの節目で、要求適合・未検証領域・負債・設計整合性・残余リスク・課題状態を見直す。
- コードの理解可能性に重要な変更があれば、必要な範囲でSDSを再評価する。全変更で全面再計算しない。

## 詳細ガイドの参照先

| 必要な内容 | 参照先 |
|---|---|
| DDD、ドメイン境界、用語 | [AI支援開発ガイド §3](ai-assisted-development.md#3-dddドメイン駆動設計) |
| SDD、要求仕様 | [AI支援開発ガイド §4](ai-assisted-development.md#4-sdd仕様駆動開発) |
| 契約設計 | [AI支援開発ガイド §5](ai-assisted-development.md#5-dbc契約による設計) |
| BDD、ATDD、TDD、テスト独立性 | [AI支援開発ガイド §6–7](ai-assisted-development.md#6-bddatdd振る舞いと受け入れの設計) |
| 変更影響評価、テスト設計、実装計画 | [`devconcord review repository`](../../.agents/skills/devconcord/references/modules/verification/devconcord-repository-review/module.md)、[`devconcord verify test-design`](../../.agents/skills/devconcord/references/modules/verification/devconcord-test-design/module.md)、[`devconcord develop implementation-plan`](../../.agents/skills/devconcord/references/modules/development/devconcord-implementation-planning/module.md) |
| 委任範囲内で複数領域の設計を具体化・改善 | [`devconcord design evolve`](../../.agents/skills/devconcord/references/modules/design/devconcord-design-orchestration/module.md) |
| 複数の開発単位で実装・検証・レビューを反復し、続行・停止判断 | [`devconcord develop iterate`](../../.agents/skills/devconcord/references/modules/development/devconcord-development-orchestration/module.md) |
| ADR | [AI支援開発ガイド §8](ai-assisted-development.md#8-adr設計判断の記録) |
| 課題管理・完成度評価 | [課題管理規約](../work-management/issue-tracking.md) |
| Self-documenting Code、SDS | [開発ガイド §2.1](ai-assisted-development.md#21-self-documenting-codeへの貢献)、[課題管理規約 §3.5](../work-management/issue-tracking.md#35-self-documenting-scoresds) |
| Doc Comments、Annotation Comments | [開発ガイド §2.2](ai-assisted-development.md#22-doc-commentsとannotation-comments) |
| 性能・堅牢性設計 | [Performance by Design §9.4](ai-assisted-development.md#94-performance-by-design)、[Robustness by Design §9.5](ai-assisted-development.md#95-robustness-by-design)、[要求仕様テンプレート](../application-design/templates/requirements.md) |
| 交換可能性・技術依存境界 | [Replaceability by Design §9.6](ai-assisted-development.md#96-replaceability-by-design)、[ADRテンプレート](../application-design/templates/adr.md) |
| セキュリティ設計・脅威分析 | [Security by Design §9.7](ai-assisted-development.md#97-security-by-design)、[Threat Modeling §11.1](ai-assisted-development.md#111-threat-modeling)、[`devconcord quality security` workflow module](../../.agents/skills/devconcord/references/modules/quality/devconcord-design-security/module.md) |
| 可観測性・診断設計 | [Robustness by Design §9.5](ai-assisted-development.md#95-robustness-by-design)、[`devconcord quality observability` workflow module](../../.agents/skills/devconcord/references/modules/quality/devconcord-observability-design/module.md) |
| 資格情報・Secretless設計 | [Secrets by Design](../application-design/secrets-by-design.md) |
| UI/UXを機能設計へ接続 | [UI/UX設計ガイド §2.5](../application-design/ui-ux-guide.md#sec02-design-to-function)、[UI/UXクイックチェック](../application-design/ui-ux-quick-reference.md) |
| プライバシー・環境衛生 | [Privacy & Environment Hygiene §11.3](ai-assisted-development.md#113-privacy-environment-hygiene) |
