# Agent Skillsの導入・同期・検証

この資料はUser Scopeを標準とするAgent Skillsの運用リファレンスです。チーム共有・CI・バージョン固定等ではProject Scopeも利用できます。初回導入の実行例は[はじめての導入と運用](getting-started.md)を参照してください。

## Skills

| Skill | 用途 |
|---|---|
| [`devconcord-reference`](../.agents/skills/devconcord-reference/SKILL.md) | ローカルDevConcordの資料を要求元Skillの版に合わせて参照 |
| [`devconcord-bootstrap-from-design`](../.agents/skills/devconcord-bootstrap-from-design/SKILL.md) | 設計要求から新規リポジトリのFoundation/Scaffold/Initial Implementationを構築 |
| [`devconcord-adopt-guidance`](../.agents/skills/devconcord-adopt-guidance/SKILL.md) | 既存プロジェクトへ共通資料を選択導入 |
| [`devconcord-sync-guidance`](../.agents/skills/devconcord-sync-guidance/SKILL.md) | 導入済み資料・Skillsをローカル変更を保護しながら同期 |
| [`devconcord-ux-functional-design`](../.agents/skills/devconcord-ux-functional-design/SKILL.md) | ユーザー目標を機能・状態・受け入れ条件へ接続 |
| [`devconcord-design-performance`](../.agents/skills/devconcord-design-performance/SKILL.md) | ワークロードに基づく性能設計と測定条件を定義 |
| [`devconcord-design-robustness`](../.agents/skills/devconcord-design-robustness/SKILL.md) | 不変条件・失敗時契約・回復・検証を設計 |
| [`devconcord-design-replaceability`](../.agents/skills/devconcord-design-replaceability/SKILL.md) | 交換価値と抽象化コストに基づき依存境界を設計 |
| [`devconcord-design-security`](../.agents/skills/devconcord-design-security/SKILL.md) | 資産・信頼境界・脅威・不変条件に応じてセキュリティ要求と検証を設計 |
| [`devconcord-repository-review`](../.agents/skills/devconcord-repository-review/SKILL.md) | 実装・設計・テスト・CI・運用記録を根拠にレビュー |
| [`devconcord-generate-agent-guidance`](../.agents/skills/devconcord-generate-agent-guidance/SKILL.md) | 実態に基づく `AGENTS.md` と `REVIEWS.md` の作成・更新 |
| [`devconcord-documentation-architecture`](../.agents/skills/devconcord-documentation-architecture/SKILL.md) | 読者タスクを中心にREADME・文書構造・導線・保守性をレビュー・改善 |

## 公式Skill名と既存インストール

DevConcord公式Skillは `devconcord-` 接頭辞を付けます。User Scopeで他の提供元のSkillと識別しやすくし、名前の衝突を減らすための命名規則です。接頭辞自体はSkillの役割や安全性を保証しません。ほかの提供元のSkillは別々に管理され、同名Skillが見つかった場合は既存の競合検出が適用されます。

旧Skill名との互換性や自動移行はありません。既存のユーザー環境・プロジェクトにある旧名SkillはDevConcordが自動削除・書き換えしません。新しい名前で導入する場合、旧名のSkillは必要性と参照元を確認し、利用者が別途整理してください。

## User Scope

User Scopeは、個人のローカル環境でSkillsを複数プロジェクトから使う標準方式です。Skillをインストールしても個々のプロジェクトへファイルやmanifestを作りません。

| 対象エージェント | ユーザースコープの配置先 | 公式仕様上の範囲 |
|---|---|---|
| OpenAI Codex | `~/.agents/skills/` | [Codex Skills](https://developers.openai.com/codex/skills)で案内されるローカルユーザーの探索先 |
| GitHub Copilot CLI | `~/.agents/skills/` | [Copilot CLI Skills](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-skills)で案内される個人Skillsの探索先。`~/.copilot/skills/`も利用でき、DevConcordは内容を変更せず同名Skillを検出する |
| Claude Code | `~/.claude/skills/` | [Claude Code Skills](https://code.claude.com/docs/en/skills)の個人Skills。このマシンのセッション向けで、Cowork/cloud session等とは共有されない |

CodexとCopilotに共通するSkillは一つの `~/.agents/skills/` パッケージとして管理し、Claude Code用は `~/.claude/skills/` に複製します。Copilotの`~/.copilot/skills/`にある同名SkillはCopilot側の探索順に従い、DevConcordは上書きしません。Copilotが`~/.agents/skills/`と`~/.claude/skills/`の両方を探索する可能性もあるため、重複可否はエージェント・版ごとに確認してください。ベンダーが同名Skillの優先順位を共通化しているとは限りません。

一度だけDevConcordの実際のGit checkoutをユーザー設定へ登録します。絶対パスは `~/.devconcord/config.json` に保存され、プロジェクトのSkill、manifest、provenanceへコピーしません。

```sh
python3 scripts/manage_skills.py config set-source \
  --source-root /absolute/path/to/DevConcord
python3 scripts/manage_skills.py config show
```

既存設定は無断で上書きされません。検証して意図的に変更するときだけ `set-source --replace` を使います。Windows、WSL2、コンテナ、リモート実行環境は別々のユーザーホーム・ファイル権限を持つ場合があり、各エージェントから同じローカルcloneを読めるとは限りません。

User ScopeのSkillsと管理情報は次のように分離されています。非DevConcord SkillやDevConcord管理外の名前は管理対象にせず、変更・削除しません。

| 用途 | 配置先 |
|---|---|
| Codex/Copilot Skills | `~/.agents/skills/` |
| Claude Code Skills | `~/.claude/skills/` |
| source設定 | `~/.devconcord/config.json` |
| manifest・lock・transactions | `~/.devconcord/skills-manifest.json`、`skills.lock`、`skills-transactions/` |

Copilot CLIが公式にサポートする`~/.copilot/skills/`は別の個人探索先です。DevConcordはそこへSkillsを導入・同期・削除しませんが、同名のSkillがある場合はUser Scopeの導入・検証を停止して、既存内容を保護します。CopilotではプロジェクトSkillsが個人Skillsより優先されるため、同名時は`doctor --target <project>`でも診断してください。

`doctor --target <project>` はユーザー状態を検証し、指定リポジトリとの同名Skillを診断します。これは静的な名前・配置診断であり、エージェントの実際の選択順位を示しません。

### ローカルDevConcord資料の参照

`devconcord-reference` はAIエージェント向けの共通参照インターフェースです。各業務Skillは必要な資料パスと、その資料が必須か任意かを決めます。別Skillの自動選択・呼び出しはエージェント間で保証されないため、共通Skillを利用できない場合は各業務Skillに記載された短い直接CLI手順を使います。各業務Skillは自身のSkill名を渡します。

```sh
python3 /absolute/path/to/DevConcord/scripts/manage_skills.py reference \
  --skill devconcord-documentation-architecture \
  --path docs/common/documentation-design.md \
  --revision installed
```

CLIは `~/.devconcord/config.json` の `source_root` を使い、設定されたローカルcheckoutから資料を読みます。`installed` は `--skill` で指定した要求元Skillのmanifest記録を使います。共通参照Skill自身や別Skillのコミットへ代替してはいけません。User Scopeでは `--target` なしが既定です。Project Scopeでは `--scope project --target <target-repository>` を追加し、そのプロジェクトのmanifestを使います。各Scopeのmanifestは独立しています。

| revision | 参照内容と保証 |
|---|---|
| `installed`（既定） | 要求元Skillのmanifestに記録されたコミットから読みます。導入先Skillのハッシュと、そのコミットのGit Skillツリーハッシュをmanifestと照合し、source identityとコミットのローカル存在を検証します。現在のHEADとの祖先関係や無関係な現在のSkillの状態は要求しません。`source_dirty=true`は厳密な版固定を証明できないため拒否します。 |
| `head` | 設定済みcheckoutの現在のコミットから読みます。未コミット変更を含まず、導入済みSkillとの版一致は保証しません。 |
| `working-tree` | checkoutの現在の作業ツリーから読みます。未コミット・未追跡の内容を含むことがあります。導入済みSkillとの版一致は保証しません。 |

Skills内のGitHub `main`リンクは閲覧用で、導入済みSkillより新しい内容を示す場合があります。版固定された正本の資料は、上記CLIでローカルGit checkoutから参照してください。オンライン資料へ自動的に切り替えることはありません。

全モードで設定とパス許可範囲を検証し、参照元のsource identityを出力します。`installed`ではmanifestのidentityを設定済みsourceと照合します。Gitコミットを読むモードは、そのコミットのtreeで `100644` / `100755` の通常ファイルだけを許可し、symlink・submodule・directoryを拒否します。`working-tree`はファイルシステム上のsymlinkとcheckout外への脱出を拒否します。どのモードもネットワークから資料を取得しません。成功時のstdoutには参照元・版・パス・本文が含まれます。失敗時は非ゼロ終了とstderrの診断を返し、stdoutに成功メタデータや部分本文を出しません。

この照合はmanifest、導入先Skill、設定済みローカルGitオブジェクトの内部整合性を確認します。manifest全体とその記録を協調して改ざんする攻撃者への暗号学的な真正性保証ではありません。また `source_tree_sha256` はSkillツリーの内容を照合するため、Skill本体が同じで資料だけが異なる複数コミットを区別しません。manifestの `source_commit` が参照するコミットは設定済みローカルGitリポジトリ内に存在する必要がありますが、現在のHEADとの祖先関係は参照の前提ではありません。manifest自体を信頼できない場合はこの参照機構の保証範囲外です。

設定ファイル欠落・不正、checkoutやスクリプトの欠落、要求元Skillの未導入、壊れたmanifest、ローカルSkill編集、source identity不一致、コミット欠落、ファイル欠落、権限不足、無効なパス、またはローカルファイルへアクセスできない実行環境では参照に失敗します。HEADやオンライン最新版へ黙って切り替えず、取得していない資料を読んだと主張してはいけません。必須資料なら安全に停止し、任意資料なら失敗を報告して自己完結したワークフローを続けられるか判断します。CLIの具体的な診断と設定手順は `manage_skills.py` とこのガイドを参照してください。

## 配置とエージェントの共用

Skillsは作業時に必要な手順だけを選択的に読み込む標準形式のワークフローです。Skillの正本はDevConcordの `.agents/skills/<skill-name>/SKILL.md` に一つだけ置きます。

以下の表は **Project Scope** でリポジトリ内にSkillを配置する場合の探索先です。User Scopeの配置先は前節を参照してください。

| エージェント | リポジトリ探索先 | 導入方法 |
|---|---|---|
| OpenAI Codex | `.agents/skills/` | `--agent codex` または `--agents` |
| GitHub Copilot | `.agents/skills/` と `.claude/skills/` 等 | `--agent copilot` または `--agents` |
| Claude Code | `.claude/skills/` | `--agent claude` または `--agents`（正本からコピーを生成） |

Skill本体は `.agents/skills/` に一つだけ置き、agent名をSkillの所有者にしません。manifest schema 2は配置パッケージごとの共有agentとSkill出典を記録します。

| 利用エージェント | 配置 |
|---|---|
| Codex / Copilot / Codex + Copilot | `.agents/skills/` 一つを共有 |
| Claude Code / Claude Code + Copilot | `.claude/skills/` 一つを共有 |
| Codex + Claude Code | `.agents/skills/` と `.claude/skills/` に同内容を生成 |
| Codex + Claude Code + Copilot | 上記二箇所。Copilotから重複発見される可能性があるため明示opt-inが必要 |

Copilotが複数のSkill探索先を実際に発見するかはホスト・版ごとに確認し、Claude Codeのsymlink等の挙動を他エージェントに一般化しません。管理ツールはCopilotがmanifest上で有効な場合、今回指定していない配置先も含めて選択Skillの操作後配置を比較します。段階的に `Claude + Copilot` を導入した後にCodexを追加する場合も、同名コピーを検出して止めます。異なる内容の同名Skillはopt-inで回避できません。同一内容の重複だけ、実機の挙動を確認したうえで `--allow-duplicate-discovery` により明示許可できます。許可はmanifestのSkill名・配置先ペアとして記録され、同じ配置先の再実行で失われません。片方だけを更新して内容がずれた場合は同期を拒否し、両方を同時に更新してください。

## 導入・同期

以下はDevConcordのcloneを `~/projects/devconcord`、対象を `~/projects/my-app` とする例です。まず `--apply` なしで計画を確認します。これは既定のdry-runで、ファイルを変更しません。

### User Scopeの導入・同期

DevConcord cloneのルートから実行します。`--scope user` を指定し、`--target` は付けません。`--apply` のない操作はdry-runです。

```sh
python3 scripts/manage_skills.py install \
  --scope user --agents codex copilot --skills devconcord-bootstrap-from-design devconcord-adopt-guidance
python3 scripts/manage_skills.py install \
  --scope user --agents codex copilot --skills devconcord-bootstrap-from-design devconcord-adopt-guidance --apply
python3 scripts/manage_skills.py validate --scope user
```

Claude Codeだけに導入する場合は `--agent claude` を選びます。Codex/Copilot用の `.agents/skills/` とClaude用の `.claude/skills/` を同時に公開するとCopilotに重複して見える可能性があります。実機で挙動を確認し、必要な場合に限り `--allow-duplicate-discovery` をdry-runと適用の両方へ指定してください。`sync --scope user` はmanifestに記録されたSkillsとagentを既定で対象とし、dry-runの後 `--apply` を指定します。

### Project Scope

以下はDevConcordのcloneを `~/projects/devconcord`、対象を `~/projects/my-app` とするProject Scopeの例です。既存CLI互換のため `--target` だけを指定してもProject Scopeですが、新規コマンドでは明示的な `--scope project` を推奨します。まず `--apply` なしで計画を確認します。これはdry-runでファイルを変更しません。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py install \
  --scope project --target ~/projects/my-app --agent codex \
  --skills devconcord-bootstrap-from-design devconcord-design-robustness
```

表示された対象・変更内容を確認した後、同じコマンドに `--apply` を追加してインストールします。全Skillsを選ぶ場合は `--skills` を省略します。既に導入したSkillの更新もdry-runで確認し、意図したものだけを適用します。

CodexとCopilot、またはClaude CodeとCopilotが同じSkillを使う場合は一回だけ導入し、同じ配置パッケージを共有します。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py install \
  --target ~/projects/my-app --agents codex copilot --skills devconcord-bootstrap-from-design
python3 ~/projects/devconcord/scripts/manage_skills.py install \
  --target ~/projects/my-app --agents claude copilot --skills devconcord-bootstrap-from-design
```

CodexとClaude Codeは探索先が分かれているため、別々の配置へ同じSkillを生成できます。3エージェント併用はCopilotが両方の探索先から同名Skillを見つけ得ます。動作を実機で確認し、重複を許容する場合に限り、dry-runと適用の両方で `--allow-duplicate-discovery` を明示します。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py install \
  --target ~/projects/my-app --agents codex claude copilot \
  --skills devconcord-bootstrap-from-design --allow-duplicate-discovery
```

同期もdry-runで確認してから適用します。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py sync \
  --scope project --target ~/projects/my-app --agent codex
python3 ~/projects/devconcord/scripts/manage_skills.py sync \
  --scope project --target ~/projects/my-app --agent codex --apply
```

意図した出典変更や巻き戻しは、出典とローカル編集を確認した後に限り `rebind-source` を明示します。rebindもローカル編集の上書きは許可せず、`--apply` が必要です。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py rebind-source \
  --scope project --target ~/projects/my-app --agent codex
python3 ~/projects/devconcord/scripts/manage_skills.py rebind-source \
  --scope project --target ~/projects/my-app --agent codex --apply
```

## 出典・manifest・ローカル変更保護

初回導入時は `.devconcord/skills-manifest.json` にSkillごとの出典識別子・完全コミットSHA、出典ツリーと導入済みツリーのSHA-256を記録します。HTTPS/SSHのscheme差やremote名変更（単一remoteの場合）は正規化し、credential・query・fragmentを識別子へ含めません。remoteのないローカルGit cloneはGit common directoryのパスを一方向SHA-256化して識別します。同じremote・履歴だけでも出典の真正性を暗号学的に証明するものではないため、更新元を信頼できることは利用者が確認してください。

User Scopeでもmanifest schema 2とhash version 2を使いますが、User Scopeのmanifestは `~/.devconcord/skills-manifest.json` です。Project Scopeの `.devconcord/skills-manifest.json` とは独立し、対象プロジェクトには個人固有パスやglobal manifestを記録しません。remoteがないUser Scope sourceはGit root historyに基づく安定した識別子を使うため、同じ履歴を持つcloneを移動して `config set-source --replace` で再登録してもパス差だけでSkillの出典が変わりません。Project Scopeの既存識別子方式は維持します。

通常同期は、記録された出典識別子、完全コミットSHAの存在と祖先関係、記録コミット時点のSkill内容と記録された出典ツリーハッシュ、導入先のローカルハッシュをそれぞれ検査します。同じ出典からの同一コミットまたは前進だけを許可し、別remote、巻き戻し、分岐、欠落/浅い履歴、比較基準不一致、ローカル編集、dirty sourceは止めます。fetch / unshallow / reset は行いません。出典URL/remoteの識別子は信頼の暗号学的証明ではなく、リモート所有権・commit署名検証も実施しません。`guidance-provenance.md` は共通ガイド資料の記録であり、Skill導入記録には使用しません。

manifest schema 2はファイル内容・種類とGitが記録する実行可能ビットをSkillの出典同一性に使います。POSIXの通常パーミッションやディレクトリ権限は含めないため、`chmod 600` と `chmod 644` のような環境差で別Skillとは判定しません。実行可能ビットは識別対象で、モードを信頼できる環境では導入先の変更も保護します。WindowsやGitの `core.fileMode=false` など、実行属性を信頼・観測できない環境ではGit treeの属性を基準にし、ローカル実行属性の変更検出が限定されます。シンボリックリンクと特殊ファイルは引き続き拒否します。旧manifest records（hash version 1、またはversionのないschema 2記録）を読み込み、対象を検証して次の適用時にversion 2へ更新します。schema 1全体も従来どおり保護的にschema 2へ移行します。

remoteを照合できない、複数remoteから現在の出典を選べない、記録基準コミットのSkill内容が記録ハッシュと一致しない場合は通常同期を止めます。導入先でSkillが編集されている、管理記録がない同名Skillがある、別の探索先と衝突する場合は上書きしません。内容を確認してローカル変更を退避・統合するか、衝突する配置を一つに整理してから再実行します。

## 中断した操作の回復

適用は対象リポジトリ内の排他ロックとトランザクションジャーナルを使い、パッケージ内容を検証してから置換し、最後にmanifestを更新します。コマンドが異常終了した場合、次のinstall/syncは残った処理を検知して停止します。まずdry-runで対象と状態を確認してください。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py recover --scope user
python3 ~/projects/devconcord/scripts/manage_skills.py recover --scope user --apply
python3 ~/projects/devconcord/scripts/manage_skills.py recover --target ~/projects/my-app
python3 ~/projects/devconcord/scripts/manage_skills.py recover --target ~/projects/my-app --apply
```

`skills.lock` が残っていて、対応プロセスが停止済みと確認できた場合だけ `recover --apply --force` を使用します。回復はジャーナル・バックアップ・現在の内容が整合するときに限ります。不明または破損したジャーナル、ジャーナル作成前の孤立ステージング、外部変更、バックアップ欠落時は自動削除・上書きせず停止し、手動調査が必要です。異なるファイルシステムを跨ぐ置換は拒否します。OS/電源障害に対する全ファイルシステムでの完全原子性は保証しません。

## 検証とトラブルシューティング

導入前にSkillの本文・同梱ファイル・出典を確認してください。インストーラーはSkill内のスクリプトを実行しませんが、Skill本文はエージェントへ指示を与えるため、信頼できない出典を信頼済みコードや安全な指示とみなしてはいけません。dry-runは対象ファイルと衝突を確認するもので、Skill内容の安全性を保証するものではありません。

Skillの発見品質（名前・frontmatter・目的を示すdescription）、選択品質（適用条件と非適用範囲）、実行品質（安全な手順、成果物、検証、結果報告）を別々に評価します。説明文が適切でSkillが発見されても、AIの実行結果が正しいとは限りません。共有Skillではベンダー固有のpermission frontmatterを使わず、Markdown参照がSkill配布単位内に解決することを確認します。

DevConcordルートで `requirements-dev.txt` の依存が導入済みのPython仮想環境を有効にして実行します。

```sh
cd ~/projects/devconcord
python3 scripts/manage_skills.py validate
python3 scripts/manage_skills.py validate --scope user
python3 scripts/manage_skills.py validate --scope project --target ~/projects/my-app
python3 scripts/validate_docs.py
python3 -B -m unittest tests.test_agent_skills tests.test_manage_skills -v
```

`validate --scope user` と `validate --scope project --target ...` は各scopeのmanifestとSkill実体のハッシュ、記録されていない/欠落したSkill、探索先の名前衝突を照合します。引数なしの `validate` はDevConcordのSkillソースを検証します。決定的な検証で確認できるのは構造・メタデータ・参照・ファイル状態です。対象エージェントでのSkill発見、選択、適用は[統合シナリオ](../tests/integration/README.md)に従って個別に評価します。

異常状態の診断や手動復旧ではmanifestとtransaction journalを保持し、内容を確認せず削除しないでください。`recover` が不整合を報告した場合は自動修復を繰り返さず、対象・manifest・transaction backupを保全して調査します。

Claude Code・Codex・Copilotでの実際の発見・呼び出し動作は各エージェントと環境のバージョンに依存します。ローカルユーザースコープの記載はCopilot CLI、Codex CLI/IDE、Claude Codeのそれぞれに対するもので、GitHub-hosted/cloud agentにユーザーのローカルSkillsや `source_root` が見えることを意味しません。静的検証や配布テストは実エージェントによる実行確認の代替ではありません。未実行のエージェントは未検証として報告してください。探索先・仕様は[Agent Skills specification](https://agentskills.io/specification)、[Claude Code Skills](https://code.claude.com/docs/en/skills)、[OpenAI Codex Skills](https://developers.openai.com/codex/skills)、[GitHub Copilot Skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)を参照してください。

## Skills非対応環境で手動利用

以前の汎用プロンプトを使っていた場合も、該当するSkillの `SKILL.md` とタスクに必要な `references/` の全文を読み、対象エージェントへ渡します。AGENTS/REVIEWS生成では依頼内容に応じたreferenceを選びます。Skillの本文だけ、あるいは共通ガイドだけで必要な詳細手順を読んだことにしないでください。ローカル共通資料が必要な場合は、該当Skillの `DevConcord References` セクションにある共通Skill利用または直接CLI手順を使います。
