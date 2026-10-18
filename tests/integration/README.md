# Bootstrap・導入・同期・設計判断の統合シナリオ

このディレクトリは、設計書から新規リポジトリを作るBootstrap、既存プロジェクトへの導入・同期について、決定的に検査できる成果物不変条件と、AIエージェントの判断を人が評価するシナリオを分離します。通常のユニットテストは固定のMarkdown出力やモデル文面に依存せず、AIモデルも呼び出しません。

## 決定的な検査

次のコマンドは検証ヘルパーと合成Git履歴の挙動を確認します。実際のAIによる導入・同期結果や設計判断の質を保証するものではありません。

```sh
python3 -B -m unittest tests.integration.test_guidance_assertions -v
```

[`assertions.py`](assertions.py) の再利用可能なチェックは、実際の導入・同期を行う一時環境を用意する半自動ハーネスから利用できます。

- `snapshot_files`、`snapshot_git_state`、`assert_paths_unchanged`、`assert_changes_within`、`assert_source_tree_unchanged`: 既存内容/ファイルモード、許可された差分範囲、資料集側のファイル・HEAD・作業ツリー無変更を確認。
- `assert_issue_records_preserved`: 既存課題IDを含む行の状態・履歴・内容が維持されたことを確認。
- `assert_markdown_links_resolve`: 導入先のMarkdown相対リンクを検査。
- `assert_provenance`: 比較基準SHA、出典ファイル、適用状態、対象ファイル、部分適用/保留理由を照合。
- `assert_idempotent`: 同じ入力への再適用前後のファイルスナップショットが同一か確認。
- `assert_bootstrap_artifacts`: Bootstrapの許可差分、必須成果物、保護ファイル、Markdownリンクを検査。
- `assert_validation_failure_kept_pending`: 検証失敗時に適用済みへ進めず、比較基準SHAも進めていないことを確認。
- `assert_no_undefined_requirement_ids`: タスクから参照するREQ IDが要求表に存在するか確認。
- `check_forward_history`: Git前進関係、同一SHA、巻き戻し、分岐、欠落コミット、浅い履歴の扱いを検査。

ヘルパーの単体テストはこれらのアサーションが誤った状態を検出することを検証します。独立したagent-runnerがないため、実際のエージェント出力へ自動適用した証拠とは区別してください。

## Agent Skillsの決定的な配布・検証テスト

[`test_agent_skills.py`](../test_agent_skills.py) はfrontmatter、Skill名とディレクトリ名、配布内リンク、各業務Skillの参照対象と直接CLIフォールバック、重複参照ファイルの不在、探索先の名前衝突を検査します。[`test_manage_skills.py`](../test_manage_skills.py) は一時リポジトリと一時ユーザーホームに対してdry-run、7通りのagent組み合わせ、段階的agent追加と全体重複状態、許可記録の再実行保持、片側同期拒否・複数側の一括同期、schema 1移行、選択インストール、HTTPS/SSH表記切替、同履歴の別remote拒否、比較基準Git treeとsource hash、前進/巻き戻し/分岐/欠落履歴、dirty source、ローカル編集保護を検査します。参照テストはUser/Project Scopeで要求元Skillと`devconcord-reference`を異なるコミットから導入し、installed参照のsource commit・Skill hashを照合します。source commit/hash改ざん、dirty source、ローカル編集、source identity不一致、旧hash version 1、新hash version 2、欠落履歴を拒否し、検証失敗時にstdout・manifest・導入先Skillが不変であることを確認します。Git treeの通常ファイル・実行ファイル・symlink・submodule・directory・欠落・空白/非ASCIIパス・不正出力と、読み取り失敗・不正UTF-8・権限エラー時のstdout抑止も検証します。User Scopeではdry-runのホーム無変更、他ユーザーSkillsの保護、configの置換・破損・symlink、source checkout移動後の版固定参照と同期、衝突診断、User Scope独立のrecoverも確認します。recover系は複数パッケージ中断、後続対象の外部変更による全体preflight拒否、破損backup、manifest書込後の完了判定、I/O失敗後の再試行を確認し、preflight拒否時の既存Skill・manifest不変をアサートします。テストは実際の `Path.home()` を変更せず、`Path.home()` を一時ディレクトリへ差し替えます。

```sh
python3 -B -m unittest tests.test_agent_skills tests.test_manage_skills -v
```

GitHub ActionsではUbuntu/Python 3.12・3.14とWindows/Python 3.14でSkills管理・文書検証テストを実行し、Git indexから作るsymlink mode等のホスト依存を抑えたfixtureも使います。これはファイルシステム操作とメタデータの決定的なテストです。実際のエージェントがSkillを発見・選択・実行することを証明しません。ローカル実行結果とGitHub-hosted Windows runnerの結果は区別して報告します。

## User Scopeの手動E2E受け入れ

実際のエージェントから個人SkillsやローカルDevConcord checkoutへアクセスできるかを評価する場合は、通常の開発者ホームを使わず、使い捨てOSユーザー、VM、または専用テストマシンで実施します。CIとユニットテストはホームに書き込みません。実エージェントE2Eは通常のCIでは実行されておらず、以下は手動評価の期待条件です。

1. 専用環境にDevConcordをcloneし、`config set-source` でその環境のローカルcloneを登録します。`config show` で正規化されたパスを確認します。
2. User Scopeのdry-runと適用を行い、対象が `~/.agents/skills/` または `~/.claude/skills/` と `~/.devconcord/` のみで、プロジェクトにはmanifestやSkillのコピーがないことを確認します。
3. `validate --scope user` と `doctor --target <temporary-project>` を実行します。DevConcord管理外のSkillと対象プロジェクトのローカルSkillが変更されないことを確認します。
4. 新規の空プロジェクトでは、エージェントをその作業ディレクトリから起動し、Bootstrap Skillにローカル参照元の版固定ガイドと設計書を使わせます。共通参照Skillが選択されない場合も直接CLIフォールバックを使えるか、必須資料が取得できないときに安全に停止するかを確認します。生成先がその対象だけであること、未実装機能・未確認コマンドを断定しないことを確認します。
5. Adoptionでは専用の既存fixtureを使い、既存構成・規約・公開リンク・独自文書とprovenanceを保護し、対象自身の検証方法を使うことを確認します。
6. source checkoutを別の絶対パスへ移動してconfigだけ更新し、元のSkill commitのreferenceとUser Scopeのno-op syncが継続できることを確認します。remote付き・remoteなしの両方を必要に応じて記録します。
7. エージェント、製品版、OS/実行環境、参照できたcommit、共通Skillの選択/直接CLI経路、生成差分、検証結果、未実施項目を記録します。Codex、Claude Code、CopilotでSkill間呼び出しが機能するか個別に確認し、確認していないエージェントは未検証とします。別マシンやクラウドでユーザーのローカルファイルが参照できない場合は、その制約を未対応または別スコープの要件として報告します。

意味的な品質、スキル選択、読者タスク達成をテスト文字列だけで合否判定しません。変更した文書は対象の既存リンク検証・サイトビルド・API生成・テスト等で確認し、DevConcordの `validate_docs.py` を外部プロジェクトへ無条件に適用しません。

## ドキュメント設計の受け入れシナリオ

[共通ドキュメント設計ガイド](../../docs/common/documentation-design.md)と[`devconcord-documentation-architecture` Skill](../../.agents/skills/devconcord-documentation-architecture/SKILL.md)の運用評価は、対象プロジェクトの既存規約・読者・公開方式を調べる手動シナリオです。ファイルリンクやSkill frontmatter等の静的検証はCIで行いますが、文書の意味的な正確さや読者タスク達成は自動検証済みとみなしません。

各シナリオでは、開始時点のHEAD・作業ツリー・文書・外部リンクを記録し、実装/設計の根拠に沿う変更だけ行います。変更後は対象プロジェクトの既存リンク検査、文書ビルド、テスト等を使い、公開URL・アンカーと無関係な成果物が保たれたことを確認します。構成差を不合格扱いせず、未実施確認は明記します。

| シナリオ | 入力・対象 | 受け入れ条件 |
|---|---|---|
| A. 新規CLI | 設計書から新規CLIをBootstrap | READMEが目的、実装済みの機能、入出力契約、実行・開発手順を実際の成果物に基づいて案内する。確認していないコマンドは検証済みとしない。GUI要件や大規模なdocs siteを追加しない |
| B. デスクトップアプリ | 初期化対象に利用者向け操作と設計資料が必要な設計書 | 利用者タスクと開発者向け資料を必要な範囲で区別し、要求・ADR・課題との参照を既存運用へ接続する。意味のないページ分割をしない |
| C. 文書整備済みプロジェクト | 既存のREADME、docs site、リンク、規約を持つリポジトリ | 既存構造・リンク・アンカー・公開URL・独自規約を維持し、合意した具体的な問題だけを改善する。導入物の無条件上書き・全体再編をしない |
| D. 文書が少ない既存プロジェクト | READMEが空または資料が乏しいが、コードと設定があるリポジトリ | コード・manifest・CIから確認した事実だけを記述し、目的・利用・ビルド・テスト・主要リンクを整備する。推測した機能、ライセンス、コマンドを追加しない |
| E. 公開ドキュメントサイト | mdBook、MkDocs、Docusaurus等の既存サイト | 既存のビルド・ナビゲーション・URL構造を維持し、必要なリンク/アンカー変更を影響分析し、対象サイトのビルドを実行する |
| F. 共通規約の同期 | 共通ドキュメント設計ガイドの旧版を適用した導入先 | 各資料の比較基準・ローカル編集・公開影響を照合し、採用/部分適用/保留/対象外を既存provenanceへ記録する。規約更新だけを理由に全資料を再編しない |
| G. 機能変更後 | API、CLI、設定、アーキテクチャ、リリース等の変更差分 | 変更に関係する利用ガイド・仕様・参照・運用手順を特定する。必要文書を更新または更新不要と判断し、コマンド例・API例・設定名と実装の整合を検証する |

シナリオの評価記録には、対象技術・読者、対象エージェント/版（実行した場合）、変更パス、確認したリンク/公開影響、実行した検証と未実施項目を含めます。AIの文書判断をテスト用固定文面と一致させることは要求せず、実際の正確さと読者タスクを根拠に評価します。

### Documentation Architecture SkillのE2E評価

意味的な品質を評価する場合は、実際の一時リポジトリで[`devconcord-documentation-architecture` Skill](../../.agents/skills/devconcord-documentation-architecture/SKILL.md)を利用し、次の証拠を残します。現在のCIはエージェントを起動しないため、E2E評価を実施していない変更については未検証と報告します。

1. A/Bは既存のCLI・desktop設計fixtureを使い、読者タスク、要求・受け入れ条件、コード/設定にある根拠、未確定事項が提案内容に反映されるかをレビューします。CLIにGUIや不要な文書サイトが追加されないこと、desktopで利用者向け操作と開発者向け設計を必要に応じて分けることを確認します。
2. C/Dは既存プロジェクトfixtureの複製と、README・docsが乏しい一時プロジェクトを用意します。既存リンク・アンカー・規約・課題IDを操作前に記録し、根拠のない機能・ライセンス・コマンドが事実として書かれていないことを確認します。
3. Eは対象のmdBook/MkDocs/Docusaurus等の実プロジェクト構成を使います。nav/sidebar、公開URL、内部リンクを記録し、そのプロジェクト固有の既存ビルドを実行します。合成サイトで実運用の公開互換性を代替しません。
4. 変更前後で [`assertions.py`](assertions.py) の `assert_changes_within`、`assert_paths_unchanged`、`assert_markdown_links_resolve`、必要に応じて `assert_idempotent` を使い、許可範囲・保持対象・リンク・再実行性を決定的に確認します。適用先に既存ビルドや検証があればそちらも実行します。
5. 意味評価では、読者が意図したタスクを完了できるか、記述がコード/仕様の証拠に一致するか、必要情報の欠落・矛盾・重複がないかを人が確認します。固定文言、文書数、短さ、単一の品質スコアを合否条件にしません。

記録にはプロジェクトとfixtureの初期HEAD、対象エージェント/版、入力したSkillと依頼文、変更パス、根拠にしたコード・設定・仕様、既存URL/アンカーの結果、実行したビルド/検証、意味評価者と未確認項目を含めます。実エージェントが使えない環境では、上記手順を未実施のままにし、静的テストだけでSkillの意味的な効果を保証しません。

特に以下の操作列を決定的な一時Gitリポジトリで確認します。

```text
install(Claude, Copilot) -> install(Codex) -> reject duplicate unless explicitly allowed
-> record allowance -> repeat install -> reject one-sided sync -> sync both -> validate
install(Source A) -> fork with shared baseline history -> reject sync(Source B)
-> rebind-source(Source B)
install(v1) -> interrupt sync(v2) -> external edit to a later recovery target
-> recover preflight rejects without changing any earlier target or manifest
```

duplicate opt-inは「異なる内容の同名Skill」や、未知の探索挙動を検証済みにするものではありません。実エージェントごとの発見範囲・選択結果は引き続き手動シナリオで確認します。

## Agent Skillsのエージェント実機シナリオ

| 対象 | 手動確認 | 証拠と制限 |
|---|---|---|
| OpenAI Codex | 一時リポジトリへ `.agents/skills/` を導入し、Skillを発見・選択できるか確認 | 対象Codexの版と実行記録を残す。静的チェックだけでは実機確認済みとしない |
| Claude Code | `.claude/skills/` の選択導入後、Skillと同梱参照を発見・利用できるか確認 | symlinkではなく生成コピーを使う。Claude Codeの版と結果を残す |
| GitHub Copilot | 対応する `.agents/skills/` からSkillを発見・参照できるか確認 | 対象Copilot環境と版を記録。未実行環境は未検証とする |
| Codex + Copilot | `.agents/skills/` の同一ファイルから両agentがSkillを発見・参照できるか確認 | 静的配置テストはあるが、実agentの発見は各環境で確認する |
| Claude Code + Copilot | `.claude/skills/` の同一ファイルから両agentがSkillを発見・参照できるか確認 | Copilotの当該探索パス対応を使う版/環境ごとに確認する |
| Codex + Claude Code | `.agents/skills/` と `.claude/skills/` の生成コピーが内容一致し、各agentが一箇所だけから発見するか確認 | CodexはClaudeの配置を探索しない前提の範囲を対象版で確認する |
| 3エージェント併用 | 両探索先に同名Skillがある時のCopilot重複表示と実行選択を記録 | 重複解決を静的テストから推定しない。通常は避け、利用者の明示確認後だけ構成する |
| 重複・競合 | 異なる内容の同名Skillを複数探索先に置き、警告・選択・表示を確認 | Claude Codeの挙動を他agentへ一般化しない。`.github/skills/`等の手動配置も含める |

実機シナリオでは入力、エージェント/版、導入Skillと出典revision、生成・変更ファイル、実行した検証、未実施の検証を記録してください。AIが必要なBootstrapや設計品質の評価は、下記の設計書fixtureを用いる手動シナリオと同様に、決定的な静的テストの結果から切り離して報告します。

## Gap Analysis Skillの手動評価シナリオ

以下は [`devconcord-gap-analysis` Skill](../../.agents/skills/devconcord-gap-analysis/SKILL.md) が対象リポジトリの目的・制約・証拠に応じて適用性と優先度を判断できるかを確認する手動シナリオです。固定文言の生成を評価せず、同じDevConcord参照版を使い、根拠の妥当性、未検証事項、Read-only動作を人が記録します。通常CIはエージェントを起動せず、下記の意味判断を検証済みとは扱いません。

| シナリオ | 対象・入力 | 確認する判断 |
|---|---|---|
| 1. 小規模CLIの全体診断 | GUIやネットワークのない小規模CLI | GUI原則を対象外とし、CLI契約・入出力・終了コード・保守性など必要な範囲を評価する。規模に合わない層や記録を要求しない |
| 2. GUIアプリの全体診断 | 画面とユーザー操作を持つデスクトップ/Webアプリ | 利用者タスク、操作状態、アクセシビリティ、プラットフォーム慣習を機能要求・実装・検証証拠へ結び付ける |
| 3. ネットワークサービスのSecurity分析 | 認証・外部入力・永続化を持つサービス | 資産、信頼境界、データ/制御フロー、攻撃経路、比例した制御、検証範囲、残余リスクを根拠から評価する |
| 4. ファイル操作アプリのRobustness分析 | 変更・取消・再試行・複数ファイル処理を持つアプリ | 原子性、部分成功、キャンセル、冪等性、整合性、復旧・診断を実装とテストで確認する |
| 5. UI技術交換のReplaceability評価 | UIフレームワーク変更が検討されているアプリ | コアへの技術漏出と交換影響を調べ、価値と費用を比較し、全依存の抽象化や無変更の交換を要求しない |
| 6. 大量データ処理のPerformance評価 | 大きな入力や高頻度処理を行う機能 | 実ワークロード・環境・アルゴリズム・資源・測定条件を確認し、根拠のない数値や未実施ベンチマークを作らない |
| 7. 文書構造と情報の正本 | README、複数ガイド、公開API説明を持つリポジトリ | 読者タスク、入口、重複・矛盾、正本、コードとの一致、リンク検証を確認し、文書数・長さで採点しない |
| 8. 前回レポートからの差分診断 | 前回レポートと指定Git基準を与える | 新規・解消・改善中・不変・悪化・再評価対象を根拠付きで分類し、変更が波及した設計や文書も確認する |
| 9. DevConcord規約を導入していない対象 | 独自の規約と文書体系を持つ既存リポジトリ | DevConcord固有の構成を強制せず、既存ルールの目的・合理性を踏まえて原則との実質的なギャップを評価する |
| 10. `AGENTS.md`と`REVIEWS.md`がない対象 | これらのファイルが存在しない対象 | 不在そのものを欠陥とせず、実際に存在する開発規約・レビュー方法と証拠を調べる |
| 11. 適用不要な原則の判断 | オフラインCLIにおけるネットワーク認証など | 対象外と判断する理由を製品特性に結び付け、証拠不足の未評価と混同しない |
| 12. 証拠不足による未評価 | 性能測定・実機検証などの証跡が与えられていない対象 | 実装欠陥と断定せず、未評価事項、確信度、判断に必要な追加証拠を示す |
| 13. 既存課題との重複検出 | 関連課題ID・完了条件・状態が記録された課題表 | 同じ問題を新規課題として重複提案せず、既存課題との関連または更新候補を示す。課題表は変更しない |
| 14. DevConcord共通参照を取得できない場合 | ローカル参照元、Skill選択、必須資料のいずれかを利用できない環境 | 実際のCLI診断を記録し、別revisionやWeb資料へ黙って切り替えず、評価主張を制限するか必須基準不足で停止する |
| 15. 未コミット変更を含む対象 | 事前スナップショット可能な作業ツリー変更を含む対象 | Git状態と差分を記録して保護し、分析目的だけで編集・stage・commitしない。変更が証拠解釈へ与える影響も明示する |

使い捨てのチェックアウトまたは専用fixtureを対象にし、開始時のHEAD、作業ツリー状態、入力資料、DevConcord参照commitを記録します。評価後に対象ファイル・HEAD・状態を比較して無変更を確認し、実施した検証と未実施の実機/性能/セキュリティ検証を分けて報告します。15シナリオすべてを一度に実施する必要はなく、変更範囲に関係するシナリオを選びます。

## AIエージェントを使う手動シナリオ

モデル出力は非決定的なため、通常CIでは実行しません。Bootstrap/導入・同期Skillsや関連規約を変更した場合は、使い捨てのローカルリポジトリと実際の対象エージェントで該当シナリオを評価します。開始前に入力設計書/資料集の版、対象のHEAD・作業ツリー状態・対象ファイル内容を記録し、シナリオ後に比較します。比較用一時リポジトリ以外の履歴を変更せず、実行していないシナリオは未実施と報告します。

### シナリオA：既存プロジェクトへの初回導入

1. [`fixtures/existing-project/`](fixtures/existing-project/) を一時ディレクトリへコピーし、対象だけをGitリポジトリとして初期化します。
2. 既存の `AGENTS.md`、`REVIEWS.md`、`ISS-0042` の完全な行とGit状態、資料集側のHEAD/状態を記録します。
3. [`devconcord-adopt-guidance` Skill](../../.agents/skills/devconcord-adopt-guidance/SKILL.md) を対象エージェントに実行します。Skill非対応環境では `SKILL.md` と [`references/workflow.md`](../../.agents/skills/devconcord-adopt-guidance/references/workflow.md) の全文を渡します。
4. 出力に対し、既存指示内容・課題レコードの保持、採用資料だけの配置、相対リンク解決、provenance SHA/状態/適用メモ、資料集側の無変更、説明されない変更がないことを確認します。
5. 適用した成果物をスナップショットし、同じ入力で同じ導入操作を再実行します。差分が不要なら再実行後の変更ファイルがゼロであることを確認します。

### シナリオB：独自変更を含む部分適用と繰り返し同期

1. シナリオAの対象リポジトリで、導入先の規約へ独自変更を加え、適用メモに未反映差分と理由を記録します。課題ID・状態・履歴も維持します。
2. 資料集の一時作業コピーで対応資料を変更してコミットし、導入先の独自ルールと競合する差分を作ります。
3. [`devconcord-sync-guidance` Skill](../../.agents/skills/devconcord-sync-guidance/SKILL.md) を実行します。Skill非対応環境では `SKILL.md` と [`references/workflow.md`](../../.agents/skills/devconcord-sync-guidance/references/workflow.md) の全文を渡します。安全に適用できる箇所だけ反映し、競合は理由付きで保留します。
4. 同じ同期を再実行し、既反映差分が複製されず、保留差分・理由と部分適用状態が保持され、独自内容が上書きされないことを確認します。
5. 検証失敗を意図的に作り、失敗時に資料行を `適用済み` とせず、比較基準SHAを進めないことを確認します。

### シナリオC：履歴関係が通常同期でない場合

一時的な資料集履歴で、前進、同一コミット、更新先が古い状態、分岐、比較元/更新先の欠落、浅いcloneを作ります。`merge-base --is-ancestor` の終了状態 `0`・`1`・その他を区別し、通常前進以外で自動適用・fetch・reset・基準SHA変更をしないこと、履歴不足を分岐と断定しないことを確認します。履歴関係の判定ロジック自体は合成履歴のユニットテストでも確認します。

### Design-to-Repository Bootstrapの手動シナリオ

[`devconcord-bootstrap-from-design` Skill](../../.agents/skills/devconcord-bootstrap-from-design/SKILL.md) を対象エージェントへ実行し、開始前後のファイルスナップショット、Git HEAD/状態、対象範囲、実行したコマンドと結果を記録します。Skill非対応環境では `SKILL.md` と [`references/workflow.md`](../../.agents/skills/devconcord-bootstrap-from-design/references/workflow.md) の全文を渡します。次の設計書fixtureを入力として利用できます。

Bootstrap対象へ先に`devconcord-bootstrap-from-design` Skillを導入する場合は、manifestがschema 2であること、両Skill探索先の全Skillがmanifestのtree hashと一致すること、探索先に余計なSkill/ファイルがないこと、他の成果物やGit履歴が存在しないことを確認します。いずれか不明なら新規対象として扱わず、既存内容を保護して停止します。比較試験では「空の対象でBootstrap後にSkillを導入」と「Skill導入後にBootstrap」の両順序を一時リポジトリで実施し、既存ファイル・履歴が保護されることを確認します。

| ケース | Fixture | 評価内容 |
|---|---|---|
| A. 小規模CLI | [`cli/design.md`](fixtures/bootstrap/cli/design.md) | GUI要件を混入せず、ストリーム入力、stderr/終了コード契約、過剰な層を避けた最小骨格とビルド/スモークテストを作る |
| B. GUIデスクトップ | [`desktop/design.md`](fixtures/bootstrap/desktop/design.md) | iced型をコアへ漏らさず、進捗・取消・破損画像の責務、要求/受け入れ条件/初期課題、UI交換境界を反映する |
| C. バックエンドサービス | [`service/design.md`](fixtures/bootstrap/service/design.md) | 原子性・冪等性・障害時契約、認証情報の扱い、必要最小限のストレージ境界と契約/統合テスト方針を記録する |
| D. 不完全・矛盾設計 | [`design-a.md`](fixtures/bootstrap/incomplete-conflicting/design-a.md)、[`design-b.md`](fixtures/bootstrap/incomplete-conflicting/design-b.md) | OS/保存データの重要な矛盾と未定義ライセンス/範囲を確定事項にせず、可逆的な基盤作業だけ進めるか判断を求める |
| E. 既存ファイルあり | [`fixtures/existing-project/`](fixtures/existing-project/) を一時ディレクトリへコピーし、既存ファイルをコミットした状態でBootstrap対象に指定 | 既存成果物・Git履歴・課題状態を保護し、対象差分を宣言して再実行で不要差分を作らない。既存プロジェクトへの規約導入が目的ならBootstrapではなくシナリオAの導入を使う |

シナリオごとに、設計書出典→TASK/REQ/NFR→設計/初期構造→課題→受け入れ条件/検証の追跡、読めなかった内容と仮定の明示、指定初期化範囲の遵守、ライセンスを勝手に選んでいないこと、`guidance-provenance.md` と設計書出典を混同しないことを確認します。対象でのビルド・テストに加えて、再実行前後のスナップショットが不変であることを確認します。決定的アサーションはAIの設計判断の正しさそのものを保証しません。

## 設計原則の適用シナリオ

これらは対応する `devconcord-ux-functional-design` / `devconcord-design-performance` / `devconcord-design-robustness` / `devconcord-design-replaceability` / `devconcord-design-security` Skillsを使った場合を含む、AIの設計・課題分解に対する手動評価です。原則名の列挙ではなく、根拠から要求、設計、受け入れ条件、検証への具体的な接続を確認します。コード実装を求めない評価では、実装済み・実測済みと誤認しないよう明記します。

| シナリオ | 観測する具体的な判断 |
|---|---|
| A. 大量データを扱う画像ブラウザー | 利用者の主要タスク、データ規模/端末を踏まえた応答設計（遅延読込・キャッシュ・仮想化の要否と費用）、破損画像/デコーダ失敗の隔離、UI表示状態とアプリ処理の境界、受け入れ条件・検証方法 |
| B. キャンセル可能なファイル転送 | 進捗/取消/再試行の目的、取消時点・部分ファイル・部分成功、原子性/冪等性/再開契約、再試行による重複・破損防止、エラー表示と復旧の検証 |
| C. UIフレームワークの交換 | UI固有依存の境界、ドメイン/ユースケース/データモデルと表示状態の分離、交換時に再実装を許す範囲、一対一ラッパーや未使用抽象化を避ける根拠、依存方向/契約の検証 |
| D. ストレージバックエンドの交換 | API形状と意味的契約の差、永続形式/マイグレーション、トランザクション/整合性、性能/セキュリティ/運用差、契約テストと統合/移行テストの役割 |
| E. 外部ファイル取込サービス | 保護資産・機密度、外部入力から保存/表示/ログまでの信頼境界とデータ流、想定する攻撃者・悪用経路・影響、最小権限・安全な既定値・攻撃面縮小の選択、認可/分離/保持削除の不変条件、拒否・部分失敗時の状態、要求・受け入れ条件・検証方法、残余リスクと未検証範囲 |

各シナリオで、(1)設計根拠、(2)要求への反映、(3)正常・異常時の状態と契約、(4)検証可能な受け入れ条件、(5)適切な依存境界、(6)過剰設計を避ける理由、(7)仮定・未検証事項があるかを記録します。根拠のない性能数値、無条件のパターン採用、無変更の交換保証を要求しません。実際の回答・成果物・使った資料版・人の判断・未実施の検証を記録し、文書ユニットテストとAI評価を別々に報告します。

Security by Designの手動評価では、シナリオEを用いて脅威分析の規模がリスクに見合うか、制御が具体的な資産・攻撃経路と結び付くかを確認します。暗号化、認証、スキャナー等の個別技術の採用数や脅威列挙数を品質の代理にせず、残余リスクを隠したり、設計回答を実装・侵入試験の証拠として扱ったりしません。このシナリオの記載は手動評価の受け入れ条件であり、今回の文書ユニットテスト実行ではAIエージェントを実行しません。
