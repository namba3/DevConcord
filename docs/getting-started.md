# はじめての導入と運用

DevConcordのAgent Skillsは **User Scope（ユーザー単位）** が標準です。一度ユーザー環境へ導入すると、対応エージェントからローカルプロジェクトで利用できます。各プロジェクトにSkillやSkill manifestをコピーする必要はありません。Skillsの利用と共通文書の導入・更新は別の操作です。

DevConcord公式Skill名には `devconcord-` が付きます。旧名Skillを導入済みの環境は自動変更されないため、新名で導入した後も既存Skillを確認し、必要なら利用者が別途整理してください。

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

**前提:** 利用するエージェントを決めます。以下はCodexとCopilotでSkillsを共用する例です。インストール時に `--skills` を省略すると、全Skillsが対象です。

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

**期待する成果物:** Codex/Copilot用なら `~/.agents/skills/`、Claude Code用なら `~/.claude/skills/` に選択したSkillsが配置され、状態・manifest・lock・復旧情報はユーザーの `~/.devconcord/` に保存されます。インストールしても対象プロジェクトにはファイルを作成しません。

## 3. 設計書から新規Bootstrapする（Codex CLI）

**前提:** Codex CLIが利用でき、登録済みのローカル参照元とグローバル `devconcord-bootstrap-from-design` SkillをCodexから読めること。`my-new-app/` は空にしておきます。グローバルSkillは対象へコピーしないため、Skill導入によってBootstrap開始状態が変わりません。

**作業ディレクトリ・変更先:** `~/projects/my-new-app/`。入力設計書は `~/projects/design/requirements.md`、ローカル参照元は `~/projects/devconcord/` です。

```sh
cd ~/projects/my-new-app
codex
```

Codexへ「`devconcord-bootstrap-from-design` Skillを使い、`~/projects/design/requirements.md` からこの空のリポジトリを初期化してください。DevConcordの資料は読み取り専用で参照し、変更先はこのリポジトリだけにしてください。未確認の機能やコマンドを事実として記載しないでください」と依頼します。

Skillが利用できない場合は、`devconcord-bootstrap-from-design` の `SKILL.md` と詳細手順を読み、両方の全文を対象リポジトリで実行中のエージェントへ渡します。

```sh
cat ~/projects/devconcord/.agents/skills/devconcord-bootstrap-from-design/SKILL.md
cat ~/projects/devconcord/.agents/skills/devconcord-bootstrap-from-design/references/workflow.md
```

**期待する成果物:** 合意した範囲のREADME、設計・要求資料、最小限の実装骨格・検証資産などです。Git初期化や技術スタックは設計と対象の状態に基づき判断します。生成された記述が設計書・実装と一致するか、人が確認してください。

## 4. 既存リポジトリへAdoptionする（Codex CLI）

**前提:** `my-app/` を既存チェックアウトとして用意し、未コミット変更を確認して保持します。既存プロジェクトにはBootstrapではなくAdoptionを使います。

**作業ディレクトリ・変更先:** `~/projects/my-app/`。参照元は `~/projects/devconcord/` です。

```sh
cd ~/projects/my-app
codex
```

「`devconcord-adopt-guidance` Skillを使い、このリポジトリの既存実装・文書・規約・リンク・履歴を調査してください。DevConcordの共通資料はローカル参照から必要な範囲だけ確認し、独自規約や未コミット変更を保護してください。導入・変更はこのリポジトリだけに行い、必要な資料を選択して理由を説明してください」と依頼します。

Skillが利用できない場合は、`devconcord-adopt-guidance` の `SKILL.md` と詳細手順を読み、両方の全文を対象コンテキストで使います。

```sh
cat ~/projects/devconcord/.agents/skills/devconcord-adopt-guidance/SKILL.md
cat ~/projects/devconcord/.agents/skills/devconcord-adopt-guidance/references/workflow.md
```

**期待する成果物:** 調査と合意に基づく必要最小限の共通資料、`AGENTS.md` / `REVIEWS.md`、採用内容を示すprovenance等です。DevConcordのSkills manifestと対象の `guidance-provenance.md` は別の記録です。適用後に差分、既存規約、リンク、provenance、対象固有の検証を確認します。

## 5. VS Code + Codex拡張でBootstrap / Adoptionする

VS Codeで開くフォルダーが作業対象です。Bootstrapなら空の `my-new-app/`、Adoptionなら既存の `my-app/` を開きます。

1. **File > Open Folder...** から対象リポジトリを開きます。
2. Codex拡張のチャットを開きます。グローバルSkillsが利用可能か確認し、BootstrapまたはAdoptionの該当Skillを指定します。
3. 参照元・変更先・設計書パスを明示し、上記シナリオと同じ指示を渡します。
4. Skillが使えない場合は、DevConcordの該当 `SKILL.md` と `references/` の必要な詳細手順を開いて全文をチャットへ貼り付けます。従来の汎用プロンプト利用者もこの方法へ移行します。DevConcord側のファイルを編集・保存しないでください。
5. 対象リポジトリで差分・リンク・既存のビルド/テストを確認します。

Codex拡張やエージェントがユーザーのホーム・DevConcord cloneへアクセスできるかは、VS Codeの実行環境と権限に依存します。実際のアクセスやSkill実行は実機で確認し、未確認の環境を対応済みとみなしません。

## 6. Claude Code・GitHub CopilotでSkillsを使う

対応するエージェントで対象プロジェクトを開き、「`devconcord-adopt-guidance` Skillを使って必要な範囲を調査してください」のように依頼します。Claude Codeの個人Skillは `~/.claude/skills/`、CodexとCopilotで共有するSkillは `~/.agents/skills/` に配置します。CLIのインストール成功と、エージェントがSkillを発見・選択・実行できることは別々に確認してください。

CopilotがCodex用 `.agents/skills/` とClaude用 `.claude/skills/` の両方を使う構成は、対応版や表示・選択動作を実機で確認してください。Claude Code、Copilot CLI、クラウドエージェントでユーザー単位のSkillsやローカルファイルアクセスが使えるかは、それぞれの実行形態によって異なります。グローバルSkillsを利用できない環境ではProject Scopeを検討します。

## 7. Project ScopeでSkillsを導入する（任意）

Project Scopeはチーム共有、CI、バージョン固定、クラウドエージェント等のためにリポジトリ内へSkillsを置く方式です。User Scopeとmanifest・復旧状態は別です。対象の作業ツリーへSkillsと `.devconcord/skills-manifest.json` を追加するため、変更を確認して管理してください。

**実行場所:** `~/projects/devconcord/`。変更先は `--target` の `~/projects/my-app/` です。

```sh
cd ~/projects/devconcord
python3 scripts/manage_skills.py install \
  --scope project --target ~/projects/my-app --agent codex \
  --skills devconcord-adopt-guidance
```

dry-runの対象と差分を確認後、同じコマンドに `--apply` を加えます。後方互換性のため `--scope` を省略して `--target` を指定した場合もProject Scopeです。User Scopeでは `--target` を指定しません。既存の非DevConcord Skills、同名Skill、ローカル編集は保護されます。

## 8. 共通ガイドのSynchronization

資料Synchronizationは、採用済みの**共通文書・規約の差分適用**です。Agent Skillsを更新する `manage_skills.py sync` とは異なります。対象に資料別provenanceと比較基準があることを先に確認します。

**作業ディレクトリ・変更先:** `~/projects/my-app/`。DevConcordは参照元です。

```sh
cd ~/projects/my-app
codex
```

`devconcord-sync-guidance` Skillを使い、ローカル変更を保護し、採用済み資料の必要な差分だけを適用するよう指示します。Skillを利用できない場合は `.agents/skills/devconcord-sync-guidance/SKILL.md` と `references/workflow.md` の全文を対象エージェントへ渡します。比較対象のDevConcordコミットやprovenanceを推測で変更しません。適用後は対象の差分、provenance、リンク、既存の文書検証を確認します。

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

`doctor` はUser Scopeの状態を検証し、任意の対象プロジェクトとの同名Skill衝突を表示します。エージェントごとの優先順位は断定しません。

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
  --skill devconcord-documentation-architecture \
  --path docs/common/documentation-design.md
```

`--revision head` は現在のコミット、`--revision working-tree` は意図的に未コミット変更を含む参照です。既定のinstalled revisionはネットワークを使いません。設定したcloneが移動した場合は、検証後 `config set-source --replace --source-root <新しい絶対パス>` で更新します。詳細な意味と失敗時の扱いは[Skill内のローカル参照手順](../.agents/skills/devconcord-documentation-architecture/references/local-devconcord.md)を確認してください。

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
