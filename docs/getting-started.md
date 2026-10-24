# はじめての導入と運用

## ふだんの開発を依頼する

作業では、内部モジュール名や実行順を指定する必要はありません。目的、対象リポジトリ、委任する範囲、守る制約を伝えてください。AIはリポジトリの指示・課題表・実装・検証結果を確認し、必要な手順と関連資料を選びます。安全に判断できる手順の違いはAIが選び、要求の意味、公開互換性、不可逆なデータ操作、重大なセキュリティリスク、外部操作など人間の判断が必要な点だけを確認します。

例: 「課題表から次の重要課題を一つ選び、承認済みの範囲で実装・検証してください。完了条件に関係する正本だけを必要に応じて更新し、失敗した検証や残る判断事項を報告してください。」

複数課題の反復、ブロッカー解消、未決事項の調査、作業再開、レビューなどの例は[開発クイックリファレンス](common/ai-development-quick-reference.md)を参照してください。詳細な論理コマンドは[ルーター](../.agents/skills/devconcord/references/routing.md)で確認できます。Skillをまだ導入していない場合は、以下のセットアップを先に行います。

DevConcordのAgent Skillsは **User Scope（ユーザー単位）** が標準です。一度ユーザー環境へ導入すると、対応エージェントからローカルプロジェクトで利用できます。各プロジェクトにSkillやSkill manifestをコピーする必要はありません。Skillsの利用と共通文書の導入・更新は別の操作です。

DevConcordの唯一の公開Skill名は `devconcord` です。従来の `devconcord-*` 名は専門ワークフローの内部モジュールIDとして残り、独立Skillではありません。既存導入は `manage_skills.py migrate` でdry-runを確認し、明示的な `--apply` で安全に移行できます。

専門Skillと検証方法は、実際の影響・不確実性・波及範囲・可逆性・証拠に応じて選び、作業途中の新しいリスクに合わせて見直します。全Skillや重い検証手法の一律実行は求めません。詳細は[Risk-Proportional Skill Application / Verification](common/ai-assisted-development.md#175-リスク比例型skill適用と検証)を参照してください。

変更前の影響評価は `devconcord review impact`、独立した検証設計は `devconcord verify test-design`、複雑な作業の段階化は `devconcord develop plan` から選べます。これは単一公開Skill内の論理ワークフローで、必要な場合だけ使います。

新規・未完成の設計を具体化したり、既存設計を複数領域にまたがって改善する作業を委任するときは、[`devconcord design evolve` workflow module](../.agents/skills/devconcord/references/modules/design/devconcord-design-orchestration/module.md)を検討できます。読み取り専用のExplore、設計成果物を扱うDesign、既存設計を扱うEvolveを依頼の範囲から選びます。Design/Evolveは実装コード変更を許可せず、重大な仕様・互換性判断は承認へ委ねます。単一領域の判断には対応する内部workflow、全体ギャップの評価には`review gap`、実装計画には`develop implementation-plan`、課題実装には`develop issue`を使います。

導入先に既存の課題表があり、その課題から次の作業を選ぶ・指定課題を実装する・範囲を区切って複数課題を進める依頼では、[`devconcord develop issue` workflow module](../.agents/skills/devconcord/references/modules/development/devconcord-issue-driven-development/module.md)を検討できます。調査だけなら読み取り専用のPlan、実装依頼ならSingleまたはユーザーが指定した範囲のBatchを選びます。workflowの選択だけで実装・課題表更新が許可されるわけではなく、課題表と導入先の完了条件が正本です。

既存設計と課題表に沿って複数の開発単位を実装・検証・レビューし、品質を再評価しながら続行・停止を判断する場合は、[`devconcord develop iterate` workflow module](../.agents/skills/devconcord/references/modules/development/devconcord-development-orchestration/module.md)を検討できます。読み取り専用のPlan、許可範囲で反復するIterate、新機能を追加しないStabilizeを依頼から選びます。単一課題や限定Batchには`develop issue`を使い、開発反復workflowも無期限の実装・自動コミットを許可しません。

作業が複数セッションにまたがる場合は、[HANDOFFテンプレート](work-management/templates/handoff.md)を使った短いスナップショットを任意で維持できます。導入先で作成する場合、正本の課題表と同じディレクトリに`HANDOFF.md`を置きます。既存の同等ファイルがあれば複製せず、移設は許可を確認します。再開時は現在のbranch・HEAD・worktree・課題表と照合し、検証結果の鮮度と現在の権限を確認します。課題表が課題状態の正本であり、HANDOFFがないことは開発の妨げになりません。

実際のブロッカーや重要な未決判断が作業を止めているときは、[`Decision Resolution & Unblocking`](../.agents/skills/devconcord/references/modules/development/devconcord-decision-resolution/module.md)を候補にできます。`decide scan/investigate/compare/recommend/resolve`は判断の発見から正本反映を、`develop unblock`は原因の解消・安全な迂回・エスカレーションを扱います。調査・推奨は承認や実装権限を与えず、このworkflowは通常の各反復に必須ではありません。

必要な場面に限り、原因不明の失敗は[`devconcord diagnose root-cause`](../.agents/skills/devconcord/references/modules/verification/devconcord-root-cause-analysis/module.md)、実際のAPI/データ形式変更は[`devconcord lifecycle compatibility`](../.agents/skills/devconcord/references/modules/lifecycle/devconcord-compatibility-migration/module.md)、リリース候補や配布・更新は[`devconcord lifecycle release`](../.agents/skills/devconcord/references/modules/lifecycle/devconcord-release-engineering/module.md)、依存の採用・変更・重大リスクは[`devconcord lifecycle dependencies`](../.agents/skills/devconcord/references/modules/lifecycle/devconcord-dependency-governance/module.md)を候補にできます。通常の開発ループの必須工程ではなく、公開パッケージ`devconcord`が未導入・利用不能でも無関係な作業を停止しません。エージェント自身のSkill発見・選択・実行品質を評価する場合は[`devconcord evaluate agent`](../.agents/skills/devconcord/references/modules/evaluation/devconcord-agent-behavior-evaluation/module.md)を使えます。利用例とE2E評価境界は[Skills一覧](agent-skills.md)と[統合評価シナリオ](../tests/integration/README.md)を参照してください。

重要な処理や障害の原因を利用者・開発者・運用者が安全に調査する必要がある場合は、[`devconcord quality observability`](../.agents/skills/devconcord/references/modules/quality/devconcord-observability-design/module.md)で診断の問いと必要な信号を設計できます。小規模なCLIのエラー出力で十分なこともあり、監視基盤・分散トレース・リモートテレメトリを一律に導入しません。

Bootstrap / Adoption / 資料Synchronizationは、導入先リポジトリを作業コンテキストとして実行します。DevConcordは読み取り専用の参照元です。Agent Skills管理CLIは別操作で、User Scopeではユーザー環境、Project Scopeでは `--target` に指定したリポジトリを変更します。

## 1. DevConcordをcloneしてローカル参照を登録する

以下の例では、DevConcord、設計書、新規対象、既存対象を `~/projects/` に配置します。既にclone済みなら再cloneしません。User Scopeの参照設定は実際のcloneを検証し、ユーザーの `~/.devconcord/config.json` に絶対パスを保存します。

**実行場所: `~/projects/`**

```sh
mkdir -p ~/projects/design ~/projects/my-new-app
cd ~/projects
git clone https://github.com/namba3/DevConcord.git devconcord
```

必要なら設計書を `~/projects/design/` に、既存プロジェクトを `~/projects/my-app/` に用意します。DevConcordディレクトリは次のようになります。

```text
~/projects/
├── devconcord/                  # Skills・共通資料の参照元
├── design/requirements.md       # Bootstrapへの入力
├── my-new-app/                  # 新規Bootstrapの変更先
└── my-app/                      # 既存プロジェクトの変更先
```

**実行場所: `~/projects/devconcord/`**

```sh
cd ~/projects/devconcord
python3 scripts/manage_skills.py config set-source \
  --source-root ~/projects/devconcord
python3 scripts/manage_skills.py config show
```

登録は `~/.devconcord/config.json` だけを作成・変更します。既存の設定は上書きしません。別の有効な設定がある場合は先に確認し、意図して変更するときだけ `set-source` に `--replace` を加えます。Windows、WSL2、コンテナ、リモート環境はそれぞれ別のホームとファイルアクセス権を持つ場合があります。実際にエージェントが使う環境で登録してください。

## 2. Agent Skillsをユーザー単位でインストールする

Skillsの標準形式と各エージェントの公式探索先に従い、CodexとCopilotで共用する `.agents/skills/`、Claude Code用の `.claude/skills/` に分けて配置します。最初にdry-runの計画を確認します。`--apply` がないコマンドはファイルを変更しません。

**前提:** 利用するエージェントを決めます。以下はCodexとCopilotで統合Skillパッケージを共用する例です。

**実行場所: `~/projects/devconcord/`。変更先: 現在のユーザー環境。**

```sh
cd ~/projects/devconcord
python3 scripts/manage_skills.py install \
  --scope user --agents codex copilot
```

出力された配置先・Skill名・競合を確認した後、同じコマンドに `--apply` を追加します。

```sh
python3 scripts/manage_skills.py install \
  --scope user --agents codex copilot --apply
python3 scripts/manage_skills.py validate --scope user
python3 scripts/manage_skills.py config show
```

Claude Codeだけを使う場合は `--agents codex copilot` の代わりに `--agent claude` を指定します。CodexまたはCopilotとClaude Codeを同時に使うと、Copilotが両方の配置から同じSkillを発見する可能性があります。ホストの挙動を実際に確認せず、3エージェント構成を既定として選ばないでください。必要な場合の重複許可は[Skills運用ガイド](agent-skills.md#配置とエージェントの共用)を参照してください。

**期待する成果物:** Codex/Copilot用なら `~/.agents/skills/`、Claude Code用なら `~/.claude/skills/` に統合 `devconcord` パッケージが配置され、状態・manifest・lock・復旧情報はユーザーの `~/.devconcord/` に保存されます。インストールしても対象プロジェクトにはファイルを作成しません。

統合Skillを導入すると統合SkillのReference moduleが含まれます。選択した内部ワークフローが必要な資料パスを決め、同じ決定的CLIを使います。要求元Skillのinstalled版を使い、必須資料が取得できないときは安全に停止し、任意資料なら自己完結した作業を続けられるか判断します。例とScope・エラー処理は[Agent Skills運用ガイドのローカル参照節](agent-skills.md#ローカルdevconcord資料の参照)を参照してください。

## 3. 設計書から新規Bootstrapする（Codex CLI）

**前提:** Codex CLIが利用でき、登録済みのローカル参照元とグローバル `devconcord manage bootstrap` workflowをCodexから読めること。`my-new-app/` は空にしておきます。グローバルSkillは対象へコピーしないため、Skill導入によってBootstrap開始状態が変わりません。

**作業ディレクトリ・変更先:** `~/projects/my-new-app/`。入力設計書は `~/projects/design/requirements.md`、ローカル参照元は `~/projects/devconcord/` です。

```sh
cd ~/projects/my-new-app
codex
```

Codexへ「`devconcord manage bootstrap` workflowを使い、`~/projects/design/requirements.md` からこの空のリポジトリを初期化してください。DevConcordの資料は読み取り専用で参照し、変更先はこのリポジトリだけにしてください。未確認の機能やコマンドを事実として記載しないでください」と依頼します。

Skillが利用できない場合は、`devconcord/SKILL.md` とBootstrap module・詳細手順を読み、必要な全文を対象リポジトリで実行中のエージェントへ渡します。

```sh
cat ~/projects/devconcord/.agents/skills/devconcord/SKILL.md
cat ~/projects/devconcord/.agents/skills/devconcord/references/modules/management/devconcord-bootstrap-from-design/module.md
cat ~/projects/devconcord/.agents/skills/devconcord/references/modules/management/devconcord-bootstrap-from-design/references/workflow.md
```

**期待する成果物:** 合意した範囲のREADME、設計・要求資料、最小限の実装骨格・検証資産などです。Git初期化や技術スタックは設計と対象の状態に基づき判断します。生成された記述が設計書・実装と一致するか、人が確認してください。

Bootstrap完了時には、既に行った初期設計を繰り返さず、解決できなかった重要な設計事項がある場合だけ後続Skillを根拠付きで提案します。後から直すと危険・高コストになる設計判断は後続へ先送りせずBootstrap中に扱います。推奨Skillは自動実行・インストールされません。共通の判断条件は[AI支援開発ガイド](common/ai-assisted-development.md)を参照してください。

## 4. 既存リポジトリへAdoptionする（Codex CLI）

**前提:** `my-app/` を既存チェックアウトとして用意し、未コミット変更を確認して保持します。既存プロジェクトにはBootstrapではなくAdoptionを使います。

**作業ディレクトリ・変更先:** `~/projects/my-app/`。参照元は `~/projects/devconcord/` です。

```sh
cd ~/projects/my-app
codex
```

「`devconcord manage adopt` workflowを使い、このリポジトリの既存実装・文書・規約・リンク・履歴を調査してください。DevConcordの共通資料はローカル参照から必要な範囲だけ確認し、独自規約や未コミット変更を保護してください。導入・変更はこのリポジトリだけに行い、必要な資料を選択して理由を説明してください」と依頼します。

Skillが利用できない場合は、`devconcord/SKILL.md` とAdoption module・詳細手順を読み、必要な全文を対象コンテキストで使います。

```sh
cat ~/projects/devconcord/.agents/skills/devconcord/SKILL.md
cat ~/projects/devconcord/.agents/skills/devconcord/references/modules/management/devconcord-adopt-guidance/module.md
cat ~/projects/devconcord/.agents/skills/devconcord/references/modules/management/devconcord-adopt-guidance/references/workflow.md
```

**期待する成果物:** 調査と合意に基づく必要最小限の共通資料、`AGENTS.md` / `REVIEW.md`、採用内容を示すprovenance等です。DevConcordのSkills manifestと対象の `guidance-provenance.md` は別の記録です。適用後に差分、既存規約、リンク、provenance、対象固有の検証を確認します。

既存リポジトリに旧 `REVIEWS.md` がある場合の移行・削除は、指示ファイル生成が採用範囲に含まれるときに `devconcord manage guidance` の `reviews` / `both` モードへ委ねます。競合や未コミット内容の保持を確認できない場合は旧ファイルも参照も保護して保留します。

共通規約の採用は、対象の要求・設計・実装がその原則に適合していることを意味しません。Adoption時に実際に確認したギャップから、必要なら横断評価用の`devconcord review gap`または専門Skillを提案します。既に有効なギャップ分析がある場合、Full Assessmentを無条件に繰り返しません。未調査の実装品質は適合・不適合とせず、追加評価が必要ならその範囲を示します。推奨Skillは自動実行・インストールされません。判断基準は[AI支援開発ガイド](common/ai-assisted-development.md)を参照してください。

## 5. VS Code + Codex拡張でBootstrap / Adoptionする

VS Codeで開くフォルダーが作業対象です。Bootstrapなら空の `my-new-app/`、Adoptionなら既存の `my-app/` を開きます。

1. **File > Open Folder...** から対象リポジトリを開きます。
2. Codex拡張のチャットを開きます。グローバルSkillsが利用可能か確認し、BootstrapまたはAdoptionの該当Skillを指定します。
3. 参照元・変更先・設計書パスを明示し、上記シナリオと同じ指示を渡します。
4. Skillが使えない場合は、`devconcord/SKILL.md` と必要な内部module・referenceを開いて全文をチャットへ貼り付けます。従来の汎用プロンプト利用者もこの方法へ移行します。DevConcord側のファイルを編集・保存しないでください。
5. 対象リポジトリで差分・リンク・既存のビルド/テストを確認します。

Codex拡張やエージェントがユーザーのホーム・DevConcord cloneへアクセスできるかは、VS Codeの実行環境と権限に依存します。実際のアクセスやSkill実行は実機で確認し、未確認の環境を対応済みとみなしません。

## 6. Claude Code・GitHub CopilotでSkillsを使う

対応するエージェントで対象プロジェクトを開き、「`devconcord manage adopt` workflowを使って必要な範囲を調査してください」のように依頼します。Claude Codeの個人Skillは `~/.claude/skills/`、CodexとCopilotで共有するSkillは `~/.agents/skills/` に配置します。CLIのインストール成功と、エージェントがSkillを発見・選択・実行できることは別々に確認してください。

CopilotがCodex用 `.agents/skills/` とClaude用 `.claude/skills/` の両方に `devconcord` を置く構成は、対応版や表示・選択動作を実機で確認してください。Claude Code、Copilot CLI、クラウドエージェントでユーザー単位のSkillsやローカルファイルアクセスが使えるかは、それぞれの実行形態によって異なります。グローバルSkillsを利用できない環境ではProject Scopeを検討します。

## 7. Project ScopeでSkillsを導入する（任意）

Project Scopeはチーム共有、CI、バージョン固定、クラウドエージェント等のためにリポジトリ内へSkillsを置く方式です。User Scopeとmanifest・復旧状態は別です。対象の作業ツリーへSkillsと `.devconcord/skills-manifest.json` を追加するため、変更を確認して管理してください。

**実行場所:** `~/projects/devconcord/`。変更先は `--target` の `~/projects/my-app/` です。

```sh
cd ~/projects/devconcord
python3 scripts/manage_skills.py install \
  --scope project --target ~/projects/my-app --agent codex
```

dry-runの対象と差分を確認後、同じコマンドに `--apply` を加えます。後方互換性のため `--scope` を省略して `--target` を指定した場合もProject Scopeです。User Scopeでは `--target` を指定しません。既存の非DevConcord Skills、同名Skill、ローカル編集は保護されます。

## 8. 共通ガイドのSynchronization

資料Synchronizationは、採用済みの**共通文書・規約の差分適用**です。Agent Skillsを更新する `manage_skills.py sync` とは異なります。対象に資料別provenanceと比較基準があることを先に確認します。

**作業ディレクトリ・変更先:** `~/projects/my-app/`。DevConcordは参照元です。

```sh
cd ~/projects/my-app
codex
```

`devconcord manage sync` workflowを使い、ローカル変更を保護し、採用済み資料の必要な差分だけを適用するよう指示します。Skillを利用できない場合は `devconcord/SKILL.md`、sync module、および同梱の `references/workflow.md` を対象エージェントへ渡します。比較対象のDevConcordコミットやprovenanceを推測で変更しません。適用後は対象の差分、provenance、リンク、既存の文書検証を確認します。

## 9. Agent Skillsの同期・検証・復旧

### User ScopeのSkills同期

**実行場所:** `~/projects/devconcord/`。対象はユーザー環境です。`--agents` を省略するとmanifestで管理されているagentを使います。

```sh
cd ~/projects/devconcord
python3 scripts/manage_skills.py sync --scope user
```

dry-runと出典・履歴・ローカル変更の検査結果を確認し、適用が必要な場合だけ同コマンドに `--apply` を追加します。

```sh
python3 scripts/manage_skills.py sync --scope user --apply
python3 scripts/manage_skills.py validate --scope user
python3 scripts/manage_skills.py doctor --target ~/projects/my-app
```

`doctor` はUser Scopeの移行状態を検証し、`--target` 指定時はProject Scopeの旧Skill残存・manifest・provenance・重複許可の状態も読み取り専用で表示します。さらに両Scope間の同名Skill衝突を報告します。保護対象の削除やmanifest修正は行わず、エージェントごとの優先順位も断定しません。

### Project ScopeのSkills同期

Project ScopeのSkillsを更新する場合は対象を明示します。

```sh
python3 scripts/manage_skills.py sync \
  --scope project --target ~/projects/my-app --agent codex
```

計画を確認後、必要な場合だけ `--apply` を追加します。検証は次のとおりです。

```sh
python3 scripts/manage_skills.py validate \
  --scope project --target ~/projects/my-app
```

通常同期は同じ出典からの前進と導入先の内容を検証します。意図した出典変更は `rebind-source`、中断操作はUser Scopeなら `recover --scope user`、Project Scopeなら `recover --scope project --target ...` をdry-runで確認します。journalやmanifestを手動削除しないでください。詳細は[Agent Skills運用ガイド](agent-skills.md)が正本です。

### ローカルの詳細資料を読む

ローカルDevConcord資料が必要なSkillは、設定ファイルの `source_root` とSkill manifestの `source_commit` を使い、通常は導入済みSkillと同じコミットの資料を読みます。例として、DevConcord cloneの `docs/common/documentation-design.md` を読むコマンドは次のとおりです。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py reference \
  --skill devconcord \
  --path docs/common/documentation-design.md
```

`installed`（既定）は要求元Skillの記録コミットとmanifest・導入Skillのハッシュを照合します。記録コミットは設定済みclone内に存在すればよく、現在のHEADとの祖先関係や無関係なSkillの状態には依存しません。`head`は現在のコミット、`working-tree`は未コミット変更を含み得るcheckoutを参照します。後者2つは導入済みSkillとの版一致を保証しません。検証失敗時にCLIはstdoutへ成功メタデータや資料の一部を出さず、別revisionへ自動切り替えません。設定したcloneが移動した場合は、検証後 `config set-source --replace --source-root <新しい絶対パス>` で更新します。ファイル種別と保証限界、共通参照Skillと直接CLIの役割、Scopeごとの参照方法は[Agent Skills運用ガイド](agent-skills.md#ローカルdevconcord資料の参照)を確認してください。

## 10. よくあるエラーと対処

| 状況 | 対処 |
|---|---|
| User Scopeのdry-runで設定がないと表示される | `config set-source --source-root <DevConcordリポジトリ>` を一度実行します。`source_root` はGit管理下のDevConcord rootでなければなりません。 |
| 既存の `config.json` を上書きできない | `config show` と設定ファイルを確認し、意図して変更する場合のみ `set-source --replace` を使います。管理中のSkill manifestは設定変更で書き換わりません。 |
| `source_root` が古い・移動した | 現在のcloneのルートとGit状態を確認し、`set-source --replace` で登録します。別出典を指す場合は同期を強行せず、出典変更の意図とSkillを確認してから `rebind-source` を検討します。 |
| 同名Skill・重複探索先が報告される | User ScopeとProject Scopeの両方を確認し、どちらのSkillを使うか選択します。エージェント間の優先順位を推測せず、明示重複は実機確認後に限ります。 |
| Skillのローカル変更が検出される | インストール先のSkillとmanifestを保全し、編集を確認・退避・統合してから再試行します。保護検査を回避しません。 |
| `reference` がコミット・ファイルを読めない | 設定、source identity、Git履歴、対象コミット・ファイルの存在、エージェントのローカルアクセス権を個別に確認します。オンライン最新版やHEADへ黙って置き換えません。 |
| `recover` が不整合を報告する | journal、manifest、バックアップを保持し、対象と状態を調査します。不明なデータを削除・上書きしません。 |
| Bootstrapが既存対象として停止する | `my-new-app/` が本当に空か確認します。既存成果物や履歴を消さず、既存プロジェクトにはAdoptionを使います。 |
| Codex CLI・VS Code拡張がSkillsや資料を読めない | 対象環境のホーム、ワークスペース権限、利用中の製品版、Skill本体とreferenceの手動入力を確認します。別マシンやクラウド環境からローカルDevConcordへアクセスできるとは限りません。 |

## DevConcord自身の検証

次の検証はDevConcordリポジトリ内で実行します。`validate_docs.py` は導入先用の汎用検証器ではありません。

```sh
cd ~/projects/devconcord
python3 scripts/manage_skills.py validate
python3 scripts/validate_docs.py
python3 -B -m unittest discover -s tests -v
npx --yes markdownlint-cli2@0.23.3 "**/*.md"
```

これらの静的検証・ユニットテストは、Codex、Claude Code、Copilot等がSkillsを発見・選択・実行する品質の証拠ではありません。実際のエージェントと版で確認した結果は分けて記録してください。対象環境・探索パス・権限・公式仕様の詳細は[Agent Skills運用ガイド](agent-skills.md)を参照してください。
