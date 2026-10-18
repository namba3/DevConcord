# Agent Skillsの導入・同期・検証

この資料は、Skillsを外部プロジェクトへ導入・共有・更新するときの運用リファレンスです。最初の導入で必要な最小手順は[はじめての導入と運用](getting-started.md)を参照してください。Skillの選択・発見・実行ワークフローは [Agent Skills一覧](../prompts/README.md#agent-skills) にあります。

## 配置とエージェントの共用

Skillsは作業時に必要な手順だけを選択的に読み込む標準形式のワークフローです。Skillの正本はDevConcordの `.agents/skills/<skill-name>/SKILL.md` に一つだけ置きます。既存プロンプトと `AGENTS.md` / `REVIEWS.md` / `docs/` は引き続き利用でき、Skills非対応環境では従来のプロンプトを使えます。

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

同期もdry-runで確認してから適用します。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py sync \
  --target ~/projects/my-app --agent codex
python3 ~/projects/devconcord/scripts/manage_skills.py sync \
  --target ~/projects/my-app --agent codex --apply
```

意図した出典変更や巻き戻しは、出典とローカル編集を確認した後に限り `rebind-source` を明示します。rebindもローカル編集の上書きは許可せず、`--apply` が必要です。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py rebind-source \
  --target ~/projects/my-app --agent codex
python3 ~/projects/devconcord/scripts/manage_skills.py rebind-source \
  --target ~/projects/my-app --agent codex --apply
```

## 出典・manifest・ローカル変更保護

初回導入時は `.devconcord/skills-manifest.json` にSkillごとの出典識別子・完全コミットSHA、出典ツリーと導入済みツリーのSHA-256を記録します。HTTPS/SSHのscheme差やremote名変更（単一remoteの場合）は正規化し、credential・query・fragmentを識別子へ含めません。remoteのないローカルGit cloneはGit common directoryのパスを一方向SHA-256化して識別します。同じremote・履歴だけでも出典の真正性を暗号学的に証明するものではないため、更新元を信頼できることは利用者が確認してください。

通常同期は、記録された出典識別子、完全コミットSHAの存在と祖先関係、記録コミット時点のSkill内容と記録された出典ツリーハッシュ、導入先のローカルハッシュをそれぞれ検査します。同じ出典からの同一コミットまたは前進だけを許可し、別remote、巻き戻し、分岐、欠落/浅い履歴、比較基準不一致、ローカル編集、dirty sourceは止めます。fetch / unshallow / reset は行いません。出典URL/remoteの識別子は信頼の暗号学的証明ではなく、リモート所有権・commit署名検証も実施しません。`guidance-provenance.md` は共通ガイド資料の記録であり、Skill導入記録には使用しません。

manifest schema 2はファイル内容・種類とGitが記録する実行可能ビットをSkillの出典同一性に使います。POSIXの通常パーミッションやディレクトリ権限は含めないため、`chmod 600` と `chmod 644` のような環境差で別Skillとは判定しません。実行可能ビットは識別対象で、モードを信頼できる環境では導入先の変更も保護します。WindowsやGitの `core.fileMode=false` など、実行属性を信頼・観測できない環境ではGit treeの属性を基準にし、ローカル実行属性の変更検出が限定されます。シンボリックリンクと特殊ファイルは引き続き拒否します。旧manifest records（hash version 1、またはversionのないschema 2記録）を読み込み、対象を検証して次の適用時にversion 2へ更新します。schema 1全体も従来どおり保護的にschema 2へ移行します。

remoteを照合できない、複数remoteから現在の出典を選べない、記録基準コミットのSkill内容が記録ハッシュと一致しない場合は通常同期を止めます。導入先でSkillが編集されている、管理記録がない同名Skillがある、別の探索先と衝突する場合は上書きしません。内容を確認してローカル変更を退避・統合するか、衝突する配置を一つに整理してから再実行します。

## 中断した操作の回復

適用は対象リポジトリ内の排他ロックとトランザクションジャーナルを使い、パッケージ内容を検証してから置換し、最後にmanifestを更新します。コマンドが異常終了した場合、次のinstall/syncは残った処理を検知して停止します。まずdry-runで対象と状態を確認してください。

```sh
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
python3 scripts/manage_skills.py validate --target ~/projects/my-app
python3 scripts/validate_docs.py
python3 -B -m unittest tests.test_agent_skills tests.test_manage_skills -v
```

`validate --target` は導入済みmanifestとSkill実体のハッシュ、記録されていない/欠落したSkill、探索先の名前衝突を照合します。引数なしの `validate` はSkillソースを検証します。決定的な検証で確認できるのは構造・メタデータ・参照・ファイル状態です。対象エージェントでのSkill発見、選択、適用は[統合シナリオ](../tests/integration/README.md)に従って個別に評価します。

異常状態の診断や手動復旧ではmanifestとtransaction journalを保持し、内容を確認せず削除しないでください。`recover` が不整合を報告した場合は自動修復を繰り返さず、対象・manifest・transaction backupを保全して調査します。

Claude Code・Codex・Copilotでの実際の発見・呼び出し動作は各エージェントと環境のバージョンに依存します。静的検証や配布テストは実エージェントによる実行確認の代替ではありません。未実行のエージェントは未検証として報告してください。探索先・仕様は[Agent Skills specification](https://agentskills.io/specification)、[Claude Code Skills](https://code.claude.com/docs/en/skills)、[OpenAI Codex Skills](https://developers.openai.com/codex/skills)、[GitHub Copilot Skills](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)を参照してください。
