# はじめての導入と運用

このガイドでは、設計書から新規リポジトリを初期化する方法と、共通資料を既存プロジェクトへ導入・更新する方法を説明します。設計書起点の新規初期化には [`bootstrap-from-design.md`](../prompts/bootstrap-from-design.md)、既存プロジェクトへの規約導入には [`adopt-guidance.md`](../prompts/adopt-guidance.md)、導入済み資料の更新には [`sync-guidance.md`](../prompts/sync-guidance.md) を使います。

## ワークフローを選ぶ

| 状況 | 使用するプロンプト | 対象 |
|---|---|---|
| 設計書をもとに空の新規プロジェクトを開発可能な状態にする | [Design-to-Repository Bootstrap](../prompts/bootstrap-from-design.md) | 新規ディレクトリ/リポジトリ。要求・構造・基盤・検証の初期状態を作る |
| すでにコードや規約があるプロジェクトに共通資料を選んで導入する | [既存プロジェクトへの初回導入](../prompts/adopt-guidance.md) | 既存成果物を保護し、共通資料を選択的に統合 |
| すでに導入済みの共通資料を更新する | [導入済み資料の同期](../prompts/sync-guidance.md) | 資料別の比較基準と保留メモを使った差分適用 |

Bootstrapは既存成果物を新規構成で上書きするためのものではありません。開始状態は、(1)空で未初期化、(2)入力一覧に明記された設計書だけ、(3)検証済みschema 2 manifestが管理するSkillsだけ、(4)その両方、(5)Git初期化済み、(6)既存プロジェクトに区別します。設計書だけの状態では指定された通常ファイルとその親ディレクトリ以外に成果物がないことを確認し、設計書を保持したまま追加作業できます。Skillsもある場合はmanifest・ツリーハッシュ・余分なファイルの検査もすべて必要です。Gitが既にある場合は再初期化せず、HEAD・履歴・remote・index・作業ツリーを確認して保持します。unborn HEADでremoteや無関係なstaged変更がない場合は追加作業を検討できます。commitや成果物が既にある場合は空と扱わず、衝突しない追加だけを許可し、競合すれば停止します。最も安全で簡単な順序は、設計書を対象外から読み、空の対象でBootstrapを実施してからSkillを導入することです。

## Agent Skillsを利用する

Skillsは作業時に必要な手順だけを選択的に読み込む標準形式のワークフローです。Skillの正本はDevConcordの `.agents/skills/<skill-name>/SKILL.md` に一つだけ置きます。既存プロンプトと `AGENTS.md` / `REVIEWS.md` / `docs/` は引き続き利用でき、Skills非対応環境では従来のプロンプトを使えます。

| エージェント | リポジトリ探索先 | 導入方法 |
|---|---|---|
| OpenAI Codex | `.agents/skills/` | `--agent codex` または `--agents` |
| GitHub Copilot | `.agents/skills/` と `.claude/skills/` 等 | `--agent copilot` または `--agents` |
| Claude Code | `.claude/skills/` | `--agent claude` または `--agents`（正本からコピーを生成） |

Skill本体は `.agents/skills/` に一つだけ置き、agent名をSkillの所有者にしません。schema 2 manifestは各配置パッケージの `agents` 配列とSkill出典・ハッシュを記録します。組み合わせは次の配置です。

| 利用エージェント | 配置 |
|---|---|
| Codex / Copilot / Codex + Copilot | `.agents/skills/` 一つを共有 |
| Claude Code / Claude Code + Copilot | `.claude/skills/` 一つを共有 |
| Codex + Claude Code | `.agents/skills/` と `.claude/skills/` に同内容を生成 |
| Codex + Claude Code + Copilot | 上記二箇所。Copilotから重複発見される可能性があるため明示opt-inが必要 |

Copilotが複数のSkill探索先を実際に発見するかはホスト・版ごとに確認し、Claude Codeのsymlink等の挙動を他エージェントに一般化しません。管理ツールはCopilotがmanifest上で有効な場合、今回指定していない配置先も含めて選択Skillの操作後配置を比較します。段階的に `Claude + Copilot` を導入した後にCodexを追加する場合も、同名コピーを検出して止めます。異なる内容の同名Skillはopt-inで回避できません。同一内容の重複だけ、実機の挙動を確認したうえで `--allow-duplicate-discovery` により明示許可できます。許可はmanifestのSkill名・配置先ペアとして記録され、同じ配置先の再実行で失われません。片方だけを更新して内容がずれた場合は同期を拒否し、両方を同時に更新してください。

DevConcordのcloneを `~/projects/devconcord`、対象を `~/projects/my-app` とした例です。まず `--apply` なしで計画を確認します。これは既定のdry-runで、ファイルを変更しません。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py install \
  --target ~/projects/my-app --agent codex \
  --skills bootstrap-from-design design-robustness
```

表示された対象・変更内容を確認した後、同じコマンドに `--apply` を追加してインストールします。全Skillsを選ぶ場合は `--skills` を省略します。既に導入したSkillの更新もdry-runで確認し、意図したものだけを適用します。

CodexとCopilot、またはClaude CodeとCopilotが同じSkillを使う場合は一回だけ導入し、同じ配置パッケージを共有します。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py install \
  --target ~/projects/my-app --agents codex copilot --skills bootstrap-from-design
python3 ~/projects/devconcord/scripts/manage_skills.py install \
  --target ~/projects/my-app --agents claude copilot --skills bootstrap-from-design
```

CodexとClaude Codeは探索先が分かれているため、別々の配置へ同じSkillを生成できます。3エージェント併用はCopilotが両方の探索先から同名Skillを見つけ得ます。動作を実機で確認し、重複を許容する場合に限り、dry-runと適用の両方で `--allow-duplicate-discovery` を明示します。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py install \
  --target ~/projects/my-app --agents codex claude copilot \
  --skills bootstrap-from-design --allow-duplicate-discovery
```

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py sync \
  --target ~/projects/my-app --agent codex
python3 ~/projects/devconcord/scripts/manage_skills.py sync \
  --target ~/projects/my-app --agent codex --apply
```

初回導入時は `.devconcord/skills-manifest.json` にSkillごとの出典識別子・完全コミットSHA、出典ツリーのSHA-256、導入済みツリーのSHA-256を記録します。HTTPS/SSHのscheme差やremote名変更（単一remoteの場合）は正規化し、credential・query・fragmentを識別子へ含めません。remoteのないローカルGit cloneはGit common directoryのパスを一方向SHA-256化して識別します。同じremote・履歴だけでも出典の真正性を暗号学的に証明するものではないため、更新元を信頼できることは利用者が確認してください。remoteを照合できない、複数remoteから現在の出典を選べない、記録基準コミットのSkill内容が記録ハッシュと一致しない場合は通常同期を止めます。HTTPSからSSHへの切替等、同一出典だと確認できるremote表記変更は通常同期できます。導入先でSkillが編集されている、管理記録がない同名Skillがある、別の探索先と衝突する場合は上書きしません。内容を確認してローカル変更を退避・統合するか、衝突する配置を一つに整理してから再実行します。`guidance-provenance.md` は共通ガイド資料の記録であり、Skillの導入記録には使用しません。

通常同期は、記録された出典識別子、完全コミットSHAの存在と祖先関係、記録コミット時点のSkill内容と記録された出典ツリーハッシュ、導入先のローカルハッシュをそれぞれ検査します。同じ出典からの同一コミットまたは前進だけを許可し、別remote、巻き戻し、分岐、欠落/浅い履歴、比較基準不一致、ローカル編集、dirty sourceは止めます。fetch / unshallow / reset は行いません。出典URL/remoteの識別子は信頼の暗号学的証明ではなく、リモート所有権・commit署名検証も実施しません。確認できない出典変更には、内容を確認して `rebind-source` を明示します。rebindも導入先ローカル編集の上書きは許可せず、明示的な `--apply` が必要です。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py rebind-source \
  --target ~/projects/my-app --agent codex
python3 ~/projects/devconcord/scripts/manage_skills.py rebind-source \
  --target ~/projects/my-app --agent codex --apply
```

適用は対象リポジトリ内の排他ロックとトランザクションジャーナルを使い、パッケージ内容を検証してから置換し、最後にmanifestを更新します。コマンドが異常終了した場合、次のinstall/syncは残った処理を検知して停止します。まず次をdry-runし、対象と状態を確認してください。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py recover --target ~/projects/my-app
python3 ~/projects/devconcord/scripts/manage_skills.py recover --target ~/projects/my-app --apply
```

`skills.lock` が残っていて、対応プロセスが停止済みと確認できた場合だけ `recover --apply --force` を使用します。回復はジャーナル・バックアップ・現在の内容が整合するときに限ります。不明または破損したジャーナル、ジャーナル作成前の孤立ステージング、外部変更、バックアップ欠落時は自動削除・上書きせず停止し、手動調査が必要です。異なるファイルシステムを跨ぐ置換は拒否します。OS/電源障害に対する全ファイルシステムでの完全原子性は保証しません。

導入前にSkillの本文・同梱ファイル・出典を確認してください。インストーラーはSkill内のスクリプトを実行しませんが、Skill本文はエージェントへ指示を与えるため、信頼できない出典を信頼済みコードや安全な指示とみなしてはいけません。dry-runは対象ファイルと衝突を確認するもので、Skill内容の安全性を保証するものではありません。

### Skill品質と検証

Skillの発見品質（名前・frontmatter・目的を示すdescription）、選択品質（適用条件と非適用範囲）、実行品質（安全な手順、成果物、検証、結果報告）を別々に評価します。説明文が適切でSkillが発見されても、AIの実行結果が正しいとは限りません。共有Skillではベンダー固有のpermission frontmatterを使わず、Markdown参照がSkill配布単位内に解決することを確認します。

DevConcordルートで `requirements-dev.txt` の依存が導入済みのPython仮想環境を有効にして実行します。

```sh
cd ~/projects/devconcord
python3 scripts/manage_skills.py validate
python3 scripts/manage_skills.py validate --target ~/projects/my-app
python3 scripts/validate_docs.py
python3 -B -m unittest tests.test_agent_skills tests.test_manage_skills -v
```

`validate` の `--target` は導入済みmanifestとSkill実体のSHA-256、記録されていない/欠落したSkill、探索先の名前衝突を照合します。引数なしの `validate` は従来どおりSkillソースを検証します。決定的な検証で確認できるのは構造・メタデータ・参照・ファイル状態です。対象エージェントでのSkill発見、選択、適用は[統合シナリオ](../tests/integration/README.md)に従って個別に評価します。

Claude Code・Codex・Copilotでの実際の発見・呼び出し動作は各エージェントと環境のバージョンに依存します。静的検証や配布テストは実エージェントによる実行確認の代替ではありません。未実行のエージェントは未検証として報告してください。

仕様・各エージェントの探索先は[Agent Skills specification](https://agentskills.io/specification)、[Claude Code Skills](https://code.claude.com/docs/en/skills)、[OpenAI Codex Skills](https://developers.openai.com/codex/skills)、[GitHub Copilot Skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)を参照してください。エージェント側の対応範囲は更新されるため、配布先の現行バージョンで確認します。

## 1. リポジトリを準備する

資料集と対象プロジェクトは、隣り合うディレクトリに clone するとパスを指定しやすくなります。

```sh
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/namba3/DevConcord.git devconcord
# 既存プロジェクトへの導入・同期で使用する場合:
git clone <対象プロジェクトの Git URL> my-app
# Bootstrapで新規作成する場合は、代わりに空の対象を用意:
mkdir -p my-new-app
```

`namba3/DevConcord` へのアクセス権があることを確認してください。HTTPS認証やSSH鍵の設定に応じて、リポジトリの **Code** メニューに表示されるURLを使えます。すでに clone 済みの場合は、この手順を飛ばしてください。`<...>` は対象プロジェクトで利用できるHTTPSまたはSSHのURLに置き換えます。資料集の作業ツリーに変更がある場合は、更新前にコミットまたは退避し、他の作業を失わないようにしてください。

例の配置では次のようになります。Bootstrapでは既存プロジェクトのcloneの代わりに空の `my-new-app` を使います。

```text
~/projects/
├── devconcord/
└── my-app/
```

## 2. 初回導入を行う

### Codex CLI

Codex CLIをインストールしてサインインした後、対象リポジトリから起動します。インストールやサインイン方法は[Codex CLI クイックスタート](https://developers.openai.com/codex/quickstart)を参照してください。

```sh
cd ~/projects/my-app
codex
```

`devconcord/prompts/adopt-guidance.md` の全文をCodexに渡し、入力欄を次のように設定します。

プロンプト本文は別のターミナルで `cat ~/projects/devconcord/prompts/adopt-guidance.md` を実行して表示し、コピーできます。本文を貼り付けた後、冒頭の入力欄に実際のパスと希望する運用を記入してください。

```text
資料集の場所: ~/projects/devconcord
導入対象: ~/projects/my-app
利用者・希望する運用: 既存の構成・設計・課題管理を尊重する
```

### VS Code拡張

1. [OpenAI Codex IDE拡張の公式手順](https://developers.openai.com/codex/ide)に従って拡張をインストールし、サインインします。
2. VS Codeで `~/projects/my-app` を開きます。
3. Codexアイコンを選ぶか、コマンドパレットから `Codex: Open Codex Sidebar` を実行します。
4. `adopt-guidance.md` の全文をCodexに渡し、資料集と対象のパスを指定します。

プロンプト全文はVS Codeで `devconcord/prompts/adopt-guidance.md` を開いてコピーするか、別ターミナルで `cat` を使って表示できます。貼り付け後、入力欄を実際のパスに置き換えます。

資料集のファイルをエージェントが読めない場合は、ワークスペースへのアクセス設定を確認するか、必要なガイド・テンプレートを対象リポジトリ内へコピーしてから実行してください。作業対象は `my-app` と明示し、資料集側のファイルは変更しないよう指示します。

初回導入時に既存の `AGENTS.md` と `REVIEWS.md` が揃っていなければ、不足するファイルを [`create-reviews-md.md`](../prompts/create-reviews-md.md) と [`create-agents-md.md`](../prompts/create-agents-md.md) で整備します。両方がない場合は `REVIEWS.md` を先に作り、`AGENTS.md` からレビュー前に読むよう指示します。既存ファイルは置き換えず、生成プロンプトの手順で内容を調査・統合してください。今回の対象外として生成しない場合は、未作成であることを導入結果に残します。

## Design-to-Repository Bootstrapを行う

新規プロジェクトのディレクトリを用意し、その対象を作業コンテキストとしてAIエージェントを起動します。対象を既存プロジェクトのGit URLからcloneする必要はありません。推奨例では設計書を対象外の `../design/` から参照します。設計書を対象内に置く場合は、入力欄でファイルを明示し、その設計書だけが存在する開始状態として扱うことを指示します。指定ファイルは保持し、生成物で上書きしません。PDF/DOCX等は利用中のエージェント環境で実際に内容を読み取れる場合に限り入力にできます。読み取りできない節・抽出結果の不確かな内容は未確認として扱います。

Bootstrap Skillを使う場合、推奨順序は空の対象でBootstrapを開始し、初期成果物を作成してから対象へ必要なSkillsを導入することです。Skillを先にインストール済みの対象を使う場合は、[`bootstrap-from-design.md`](../prompts/bootstrap-from-design.md) にあるschema 2 manifest・ツリーハッシュ・対象内の他成果物・Git履歴の検査をすべて満たさなければ進めません。Codex / Claude Code / CopilotいずれでもSkillの利用と対象へのファイル変更を区別し、agentの探索挙動が未確認ならプロンプト全文を使う手順へフォールバックします。

[`bootstrap-from-design.md`](../prompts/bootstrap-from-design.md) の全文をエージェントへ渡し、入力欄を指定します。

```text
設計書のパス（複数可）: ../design/requirements.md, ../design/architecture.md
初期化対象ディレクトリ: .
プロジェクト名: Example App
技術的制約: 設計書に記載の内容を参照
初期化範囲: 開発基盤のみ
追加指定: 設計書をリポジトリへコピーしない。対象外の設計書は読み取り専用で参照する
```

設計書を対象内に配置したい場合は、例えば `./design/requirements.md` と `./design/architecture.md` を入力として明示し、対象にそのファイルと親ディレクトリ以外の成果物がないことを確認します。Bootstrapは指定された設計書を読み取り専用入力として保持し、別ファイルの生成・追記で構成します。対象内設計書とSkillsを同居させる場合はmanifest・ツリーハッシュ等のSkills検証条件も必要です。

作業開始前に設計書の矛盾・不足と対象ディレクトリのGit/ファイル状態を確認します。曖昧なライセンスや技術選択を勝手に決めず、重要な不明点は未決事項として記録します。実装のない設計制約を実装済みの事実として `AGENTS.md` / `REVIEWS.md` に記載しないよう、既存の指示ファイル生成プロンプトの方針を再利用します。

初期化後は、要求・ADR・課題・初期構造・受け入れ条件が設計書出典へ必要な範囲でつながること、既存ファイル/履歴が保持されたこと、実行可能なビルド・テストと未実施の将来検証が分けて報告されていることを確認します。初期化は機能完成を意味しません。設計書出典の記録は共通資料の `docs/guidance-provenance.md` と別であることにも注意してください。

## 3. 導入結果を確認する

AIの報告だけで完了とせず、対象リポジトリで次を確認します。

- 選択した資料がプロジェクトの構成や利用技術に合っている。
- 既存の `AGENTS.md`、`REVIEWS.md`、課題表、設計文書の有効なルールが保持されている。
- 新規・変更した文書の相対リンクが対象リポジトリ内で解決する。
- `AGENTS.md` からレビュー前に `REVIEWS.md` を読むよう指示されている。
- 課題ID、状態、優先度などを既存運用と矛盾させていない。
- 要求・設計・課題・リスク・検証証跡が必要な範囲で相互参照され、対応作業の二重台帳がない。
- `実装済み` と `検証済み` が区別され、未実施の確認や残余リスクが成功扱いになっていない。
- Self-documenting Codeをコードの意味・責務・契約・振る舞いを表す品質原則として扱い、コメント削減や好みの命名規則にしていない。
- 公開・重要APIのDoc Commentsを対象言語の標準方式で扱い、Annotation Commentsは必要な未解決事項の表示に使い、重要な作業だけ既存課題IDへ関連付けている。
- SDSを採用する場合、その評価軸と重みが共通規約と一致し、既存の総合完成度と分離されている。コードを成果物としない場合は対象外の理由が記録されている。
- シークレット検査が必要なプロジェクトでは、Markdownだけでなくソース、環境設定、YAML/JSON等の対象をカバーする専用スキャナーを選び、既存CIやローカル手順で結果を確認する。検査結果や報告に秘密の値を転載しない。
- ソース、資料、設定、ログ、AI報告に不要な個人情報・秘密情報・個人環境情報が含まれず、必要な絶対パスはOS/API契約やテスト等の理由が明確である。
- 性能が重要な機能ではワークロード・対象環境・検証方法が整理され、実測の有無と過剰最適化を避ける方針が明らかである。
- 変更差分を読み、不要な資料やソースコード変更が含まれていない。
- 保留した規約、未確認事項、検証できなかった項目が記録されている。

導入した共通資料の出所と版は、対象リポジトリに `docs/guidance-provenance.md` を作り、次の形式で記録します。

```markdown
# 共通資料の適用記録

- 資料集: <リポジトリURL>
- 確認済み資料集コミット: <40桁のコミットSHA>
- 確認日: YYYY-MM-DD

| 資料集のパス | 導入先のパス | 比較基準コミット | 状態 | 適用メモ・保留差分 |
|---|---|---|---|---|
| `docs/common/ai-assisted-development.md` | `docs/ai-assisted-development.md` | `<40桁のコミットSHA>` | 適用済み | プロジェクト用に見出しを調整 |
| `docs/application-design/ui-ux-guide.md` | `docs/ui-ux-guide.md` | `<40桁のコミットSHA>` | 部分適用 | トークン節は適用済み。アクセシビリティ節の競合を保留 |
```

コミットSHAはブランチ名や `latest` ではなく、実際に確認した資料集のコミットを記録します。`確認済み資料集コミット` は資料集全体を確認した地点、各資料の `比較基準コミット` はその資料の後続差分を調べる起点です。比較基準コミットは適用完了の印ではありません。どの変更を反映したか、何を保留したかは `状態` と `適用メモ・保留差分` に記録します。

初回導入では、採用・部分適用・保留と判断した資料ごとに、その判断に使った完全SHAを比較基準コミットへ記録します。状態は、適用またはプロジェクト向けに調整した範囲を反映済みなら `適用済み`、一部を反映し残りがあるなら `部分適用`、選択したが競合等で適用を保留しているなら `保留` とします。初回に一部または全部を保留した場合は、反映した範囲、未適用差分、保留理由を適用メモへ記録します。プロジェクトで採用しない資料は `対象外` とし、比較基準を `—` にして理由をメモへ残します。

以後の同期では、比較基準コミット以降の差分に加え、適用メモに残る未適用差分も候補として確認します。導入先の実体とメモを照合し、既に反映した内容を重複適用せず、保留中の内容を見落とさないようにします。全差分を適用した資料は基準を今回確認したSHAへ進めます。同期中に一部を保留した資料は基準を進めず、確認済み資料集コミットだけ更新できます。状態は `適用済み`、`部分適用`、`保留`、`対象外` を使います。資料の移動・改名で配置が異なる場合も、資料集のパスと導入先のパスを対応づけてください。

従来形式の `適用済みコミット` 列は `比較基準コミット` の旧名称として読みます。値はそのまま保持し、適用状態は列の値だけから推定しません。既存ファイルを更新する際は、列名だけ新名称へ変更して構いませんが、SHA、状態、適用メモを一緒に見直し、根拠なく書き換えたり履歴を初期化したりしないでください。基準SHAや適用範囲を確認できない古い記録は、導入先の内容・Git履歴・既存メモを調べ、なお特定できない場合は不明と記録して利用者に確認します。

採用しなかった資料やプロジェクト向けに変更した資料も状態とメモに記録してください。

## 4. 導入済みの資料を更新する

差分の適用前に、資料集リポジトリ内で比較基準SHAと更新先SHAが実在する完全なコミットであることを確認します。通常の同期は比較基準が更新先の祖先である場合に限ります。

```sh
git cat-file -e "$BASE_SHA^{commit}"
git cat-file -e "$TARGET_SHA^{commit}"
git merge-base --is-ancestor "$BASE_SHA" "$TARGET_SHA"
```

`merge-base` の終了状態 `0` は前進関係、`1` は祖先関係なし、それ以外はGitコマンドの失敗です。終了状態 `1` なら逆向きの祖先関係も調べ、更新先が古い場合と分岐を区別します。両SHAが同じ場合は差分なしの再同期とし、不要な編集・記録変更を行いません。浅いcloneで祖先関係を確定できない場合は分岐と断定せず、安全な同期を停止します。

SHA欠落、分岐、巻き戻し、浅い履歴、Gitコマンド失敗のいずれも、通常の前進同期として自動適用してはいけません。必要な情報と対処案を報告し、利用者の明示的な許可なく `fetch`、`unshallow`、`reset`、比較基準の書き換えを行いません。資料ごとの比較基準と部分適用・保留メモは引き続き維持します。同期プロンプトの[安全な履歴判定](../prompts/sync-guidance.md)も参照してください。

1. 資料集の作業ツリーを確認し、変更を保護したうえで必要なら最新の `main` を取得します。確認地点を `git rev-parse HEAD` で記録します。
2. 対象リポジトリの `docs/guidance-provenance.md` と作業ツリーを確認します。
3. 更新用の [`sync-guidance.md`](../prompts/sync-guidance.md) を使い、資料別の比較基準コミットと今回確認するコミットを指定します。
4. 提案された差分をレビューし、対象プロジェクトに必要な変更を適用します。
5. 検証後にのみ、適用記録のコミットSHA・日付・採用資料を更新します。

資料集の更新を追跡する際は、プロジェクト固有の変更を上書きせず、採用していない資料の変更を自動適用しないでください。詳細は [`sync-guidance.md`](../prompts/sync-guidance.md) に従います。

## 公式のCodex手順

CLIやIDE拡張の操作は更新される場合があります。最新の操作方法は[Codex CLI](https://developers.openai.com/codex/cli)と[Codex IDE拡張](https://developers.openai.com/codex/ide)の公式ドキュメントを参照してください。

## 困ったとき

- **資料集をcloneできない:** リポジトリへのアクセス権、HTTPS認証、SSH鍵を確認します。利用できるURLはGitHubのリポジトリ画面で確認します。
- **Codexが別ディレクトリの資料を読めない:** 利用中のCLI・IDEのワークスペース／ファイルアクセス設定を確認します。設定変更ができない場合は、プロンプト本文を貼り付け、必要な資料だけを対象リポジトリ内の一時フォルダーにコピーして参照させます。一時ファイルは導入後に削除し、元の資料集は編集しないよう指定します。
- **適用済み資料の配置が標準例と違う:** `guidance-provenance.md` の「資料集のパス」と「導入先のパス」に実際の対応を記録し、更新プロンプトへ渡します。
