# はじめての導入と運用

このページは、DevConcordを初めて利用する開発者向けの実行例です。標準方式は **Target-centric** です。Bootstrap / Adoption / Synchronizationのプロンプトを実行するときは導入先を作業コンテキストにし、DevConcordは読み取り専用の参照元として指定します。Agent Skills管理CLIは別操作で、どのディレクトリから実行しても `--target` に指定したリポジトリを変更します。

## まず選ぶ

| 目的 | 作業対象 | 使うもの |
|---|---|---|
| 設計書から新しいプロジェクトを始める | 空の `my-new-app/` | [`bootstrap-from-design.md`](../prompts/bootstrap-from-design.md) |
| 既存プロジェクトへ共通資料を導入する | 既存の `my-app/` | [`adopt-guidance.md`](../prompts/adopt-guidance.md) |
| 導入済みの共通資料を更新する | 既存の `my-app/` | [`sync-guidance.md`](../prompts/sync-guidance.md) |
| 導入済みAgent Skillsを更新する | manifest管理下の `my-app/` | [`manage_skills.py sync`](agent-skills.md) |

**BootstrapとAdoptionは別の作業です。** 既存ファイルや履歴がある対象へBootstrapを実行しないでください。また、新規Bootstrapの前にSkillをインストールしないでください。Skillだけの状態も追加のmanifest・ツリー検証が必要な開始状態になるため、先にBootstrapを終え、必要なSkillはその後に導入するのが簡単で安全です。

## 1. cloneして作業場所を用意する

以下は `~/projects/` の下にDevConcord、設計書、新規対象、既存対象を置く例です。既にclone済みのリポジトリは再cloneしないでください。既存プロジェクトをcloneする場合、コマンド実行時に自分が利用できるGit URLを入力します。

**実行場所: `~/projects/`**

```sh
mkdir -p ~/projects/design ~/projects/my-new-app
cd ~/projects
git clone https://github.com/namba3/DevConcord.git devconcord
# 既存プロジェクトをまだcloneしていない場合だけ実行する:
read -r -p "既存プロジェクトのGit URL: " REPO_URL
git clone "$REPO_URL" my-app
```

`my-new-app/` が既に存在する場合は、中身を確認し、空でないディレクトリをBootstrap対象にしないでください。設計書を `~/projects/design/` に配置してください。以降の例では `requirements.md` を入力設計書とします。実際のファイル名が異なる場合は、指示例のパスを置き換えます。ディレクトリは次のようになります。

```text
~/projects/
├── devconcord/                  # 共通資料とプロンプト。参照元
├── design/requirements.md       # Bootstrapへの入力
├── my-new-app/                  # Bootstrapの変更先。開始時は空
└── my-app/                      # 既存リポジトリ。Adoption/同期の変更先
```

DevConcordに未コミット変更がある場合は、内容を確認せず更新・破棄しないでください。以下の操作ではDevConcordのファイルを編集しません。

## 2. Codex CLIで新規Bootstrapする

**前提:** Codex CLIが利用可能で、設計書を読めること。`my-new-app/` は空であること。Bootstrap前にAgent Skillsを導入しません。

**作業ディレクトリ:** Codexを起動する前に `~/projects/my-new-app/` へ移動します。入力は `~/projects/design/requirements.md`、変更先は `~/projects/my-new-app/`、参照元は `~/projects/devconcord/` です。

**実行場所: `~/projects/my-new-app/`**

```sh
cd ~/projects/my-new-app
codex
```

Codexのチャットには、別ターミナルから次のコマンドで表示したプロンプト全文を貼り付けます。コマンドを実行するターミナルはどこでも構いません。

```sh
cat ~/projects/devconcord/prompts/bootstrap-from-design.md
```

そのプロンプトの入力欄を、例えば次のように指定してください。

```text
設計書のパス（複数可）: ~/projects/design/requirements.md
初期化対象ディレクトリ: ~/projects/my-new-app
プロジェクト名: 設計書に記載された名称を使用
技術的制約: 設計書に記載された制約を使用
初期化範囲: 最小実装骨格まで
Git初期化: 空の対象に限り必要性を確認して実施
追加指定: ~/projects/devconcord の資料は読み取り専用で参照し、変更先は ~/projects/my-new-app のみとする。未確認の機能・ライセンス・コマンドを事実として記載しない
```

**期待する成果物:** 合意した初期化範囲に応じたREADME、設計・要求資料、最小限のプロジェクト骨格と検証資産などです。設計書と作業前の状態を照合し、未実装機能を完成済みと記載していないことを確認します。

**実行後の確認:** Git初期化を行った場合は `~/projects/my-new-app/` で `git status --short` を確認します。README・生成ファイル・リンク・要求出典・実装状態もレビューしてください。技術スタックが確定した後、そのプロジェクトの開発手順に記載されたビルド・テスト・検証だけを実行してください。Bootstrapは機能完成や全テスト成功を意味しません。

## 3. Codex CLIで既存プロジェクトへAdoptionする

**前提:** `my-app/` をclone済みまたは既存チェックアウトとして用意し、現在の作業ツリーを把握していること。未コミット変更がある場合は、作業開始時点を記録し、保持するよう指示します。

**作業ディレクトリ:** `~/projects/my-app/`。参照元は `~/projects/devconcord/`、変更先は `~/projects/my-app/` です。

**実行場所: `~/projects/my-app/`**

```sh
cd ~/projects/my-app
codex
```

Codexへ渡すAdoptionプロンプトは次のコマンドで表示できます。

```sh
cat ~/projects/devconcord/prompts/adopt-guidance.md
```

プロンプトの入力欄の記入例:

```text
資料集の場所: ~/projects/devconcord
導入対象: ~/projects/my-app
利用者・希望する運用: 既存の構成・設計・課題管理・文書リンクを保護し、必要な共通資料だけ選択導入する
Agent Skills導入: 今回は導入しない
```

**期待する成果物:** 調査・合意した範囲の資料や指示ファイル、採用・保留の範囲を記録するprovenanceなどです。既存の有効な規約・要求ID・課題・リンクを無条件に再編しないでください。

**実行後の確認:** `~/projects/my-app/` で `git status --short` と `git diff --check` を実行し、差分をレビューします。課題表、`AGENTS.md` / `REVIEWS.md`、相対リンク、provenanceと適用内容を確認し、対象プロジェクト既存の文書検証・ビルド・テストを実行します。DevConcord自身の検証器は、導入先用としてそのまま実行するものではありません。

## 4. VS Code + Codex拡張でBootstrapまたはAdoptionする

CLIと同様に、**VS Codeで開くフォルダーが作業対象**です。Bootstrapなら空の `~/projects/my-new-app/`、Adoptionなら既存の `~/projects/my-app/` を開きます。DevConcordフォルダーを作業対象として開いてプロンプトを実行しないでください。

1. VS Codeの **File > Open Folder...** から対象リポジトリを開きます。
2. Codex拡張のサイドバーを開きます。コマンドパレットで `Codex: Open Codex Sidebar` を選べます。
3. VS Codeの統合ターミナルで `cat ~/projects/devconcord/prompts/bootstrap-from-design.md` または `cat ~/projects/devconcord/prompts/adopt-guidance.md` を実行し、該当する全文をCodexチャットへ貼り付けます。
4. Bootstrapなら「2. Codex CLIで新規Bootstrapする」、Adoptionなら「3. Codex CLIで既存プロジェクトへAdoptionする」の入力例を使い、参照元・変更先・読み取り専用の境界を指定します。
5. 提案された差分を確認し、同節の実行後チェックを行います。

プロンプトファイルをVS Codeで開く場合はDevConcordの内容を編集・保存しないでください。ワークスペース外のファイルにアクセスできない環境では、プロンプト全文をコピーして渡します。実際の拡張UI・アクセス設定はバージョンにより異なるため、必要なら[公式Codex IDE手順](https://developers.openai.com/codex/ide)を確認してください。

## Agent Skillsを利用する

5番目のシナリオはAgent Skillsの導入です。インストールはプロンプト実行とは別の操作です。`manage_skills.py` の既定の出典はそのスクリプトを含むDevConcordリポジトリで、`--target` が変更先です。例ではBootstrapまたはAdoption完了後の `my-new-app/` を対象に、Codex用Bootstrap Skillだけを導入します。

**前提:** 対象に対するSkills導入が初回、またはmanifestで管理されたSkillであること。導入先のローカル変更を保護するため、まずdry-runします。

**実行場所:** 下の例は `~/projects/` から実行します。`--target` が実際の変更先を指定します。

```sh
cd ~/projects
python3 ~/projects/devconcord/scripts/manage_skills.py install \
  --target ~/projects/my-new-app --agent codex \
  --skills bootstrap-from-design
```

計画に表示された対象、Skill名、競合を確認します。問題がなければ、次の適用コマンドを実行します。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py install \
  --target ~/projects/my-new-app --agent codex \
  --skills bootstrap-from-design --apply
```

**期待する成果物:** 対象の `.agents/skills/bootstrap-from-design/` と `.devconcord/skills-manifest.json` です。CLIはSkillを対象へコピーします。DevConcordのSkill正本を変更しません。

**利用時の指示例:** インストール後、Codexで対象リポジトリを開き、「`bootstrap-from-design` Skillを使い、指定した設計書に基づいてこの新規プロジェクトを初期化してください。変更先はこのリポジトリだけにしてください」と依頼します。開始状態の条件が複雑になるため、通常は先にBootstrapプロンプトを実行し、その後でSkillを導入してください。

**注意:** Bootstrap Skillを先に入れて空の対象へBootstrapする方法は可能ですが、対象状態の判定が増えるため、まずBootstrapを完了してからSkillsを導入してください。Claude CodeまたはCopilotとの共用例は次節、出典・属性・重複・復旧の詳細は[Agent Skills運用ガイド](agent-skills.md)を参照します。

## 6. Claude Code・GitHub CopilotでSkillsを使う

インストール先を管理CLIの `--agent` / `--agents` で選び、その後、該当エージェントで **同じ対象リポジトリ** を開きます。CodexとCopilotは `.agents/skills/` を共用できます。Claude CodeとCopilotは `.claude/skills/` を共用できます。以下はCopilotとClaude Code用に、既存のBootstrap Skillを選んでdry-runし、確認後に適用する例です。

**実行場所:** `~/projects/`。dry-runの計画を確認後、問題がなければ適用コマンドを別途実行します。変更先は `--target` で明示します。

Copilot向けdry-run:

```sh
cd ~/projects
python3 ~/projects/devconcord/scripts/manage_skills.py install \
  --target ~/projects/my-new-app --agent copilot --skills bootstrap-from-design
```

計画を確認後、Copilot向け適用:

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py install \
  --target ~/projects/my-new-app --agent copilot --skills bootstrap-from-design --apply
```

Claude Code向けdry-run:

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py install \
  --target ~/projects/my-new-app --agent claude --skills bootstrap-from-design
```

計画を確認後、Claude Code向け適用:

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py install \
  --target ~/projects/my-new-app --agent claude --skills bootstrap-from-design --apply
```

**期待する成果物:** Copilot用なら `.agents/skills/`、Claude Code用なら `.claude/skills/` にSkillコピーとmanifest記録ができます。導入後にCopilotまたはClaude Codeで `my-new-app/` を開き、Skillが発見・選択されるか確認します。インストール成功はエージェントでの発見・実行を保証しません。

**利用時の指示例:** 対象を開いたCopilotまたはClaude Codeに「`bootstrap-from-design` Skillを使い、`~/projects/design/requirements.md` を入力としてこのリポジトリを初期化してください。DevConcordは読み取り専用の参照元とし、変更先はこのリポジトリだけにしてください」と依頼します。Skillを明示して依頼しても、エージェントが対応Skillを認識・利用することは別途確認してください。

**注意:** 三者併用ではCopilotが複数探索先から同じSkillを見つける可能性があります。必要な組合せの重複挙動を実機で確認し、明示許可が必要なら[運用ガイド](agent-skills.md#配置とエージェントの共用)を参照してください。エージェントの起動オプションはここでは指定しません。利用中の版の公式手順に従い、対象リポジトリを開きます。

## 7. 導入済み共通ガイドをSynchronizationする

これは、DevConcordから以前採用した**文書・規約の差分適用**です。Agent Skillsのファイルを同期する `manage_skills.py sync` とは別操作です。`my-app/` のprovenanceに資料別の比較基準が記録されている場合に使います。記録がなければ通常のSynchronizationとして開始せず、初回Adoptionの扱いを確認します。

**実行前:** 資料集の現在の完全コミットと導入先の変更を確認します。

```sh
git -C ~/projects/devconcord rev-parse HEAD
git -C ~/projects/my-app status --short
```

**作業ディレクトリ:** Codex等のエージェントを `~/projects/my-app/` で起動します。DevConcordのプロンプトと共通資料は読み取り専用の参照元です。

```sh
cd ~/projects/my-app
codex
```

別ターミナルで `cat ~/projects/devconcord/prompts/sync-guidance.md` によりプロンプトを表示して渡します。入力例の「今回確認するコミット」には、`git -C ~/projects/devconcord rev-parse HEAD` の結果を指定します。

```text
資料集の場所: ~/projects/devconcord
導入対象: ~/projects/my-app
今回確認するコミット: <上のコマンドが出力した完全なコミットSHA>
更新方針: 既存のプロジェクト固有ルール、未コミット変更、資料別provenance、リンクを保護し、採用済み資料の必要な差分だけを適用する
Agent Skills同期: 今回は同期しない
```

**期待する成果物:** 同意された資料差分のみが `my-app/` に反映され、変更した資料のprovenanceが実際の適用状況に合います。保留や対象外の差分は理由とともに既存記録へ残します。エージェントが `devconcord/` 側に変更を提案した場合は適用しないでください。

**実行後の確認:** `my-app/` で `git status --short`、`git diff --check`、変更文書のリンク検証と対象固有の文書ビルド/テストを実施します。provenanceのSHAは実際に比較した値、状態は実際に適用した範囲と一致させます。異なる履歴・浅い履歴・比較基準不明などの扱いは[同期プロンプト](../prompts/sync-guidance.md)を参照し、fetch・reset・基準SHA変更を独断で行いません。

## 8. 導入済みAgent Skillsを同期する

これは、manifestで管理された**Skillパッケージの更新**です。共通ガイドのSynchronizationではありません。`sync` は記録済み出典・履歴・導入先ハッシュを検証します。出典変更、履歴巻き戻し、未追跡のSkillsを通常同期で上書きしません。

**実行場所:** `~/projects/`。対象とエージェントはCLI引数で明示します。

```sh
cd ~/projects
python3 ~/projects/devconcord/scripts/manage_skills.py sync \
  --target ~/projects/my-app --agent codex
```

dry-runの計画をレビューし、問題なければ同じコマンドに `--apply` を加えます。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py sync \
  --target ~/projects/my-app --agent codex --apply
```

**期待する成果物:** manifestに記録されたCodex向けSkillsだけが安全に更新され、`my-app/` のmanifestが更新されます。別agent用パッケージを同期する場合はmanifest上の構成に合わせて `--agent` または `--agents` を指定します。

**実行後の確認:** `python3 ~/projects/devconcord/scripts/manage_skills.py validate --target ~/projects/my-app` を実行し、さらに対象で `git -C ~/projects/my-app status --short` を確認します。出典変更や中断操作の回復は、[Agent Skills運用ガイド](agent-skills.md)の `rebind-source` / `recover` の説明を読み、状況を確認してから行います。

## 9. 検証コマンド

以下は検証対象ごとに実行場所が異なります。

**導入先リポジトリで実行:** 変更範囲を確認し、対象プロジェクトが既に持つ検証手段（Markdownlint、リンク検査、サイトビルド、単体テストなど）を使います。すべてのプロジェクトに共通のテストコマンドはありません。

```sh
cd ~/projects/my-app
git status --short
git diff --check
```

導入済みSkillsを検証するCLIは、DevConcord内のスクリプトから導入先を指定します。作業ディレクトリは任意です。

```sh
python3 ~/projects/devconcord/scripts/manage_skills.py validate \
  --target ~/projects/my-app
```

**DevConcord自身の資料・テストを検証:** ここで初めてDevConcordリポジトリへ移動します。`validate_docs.py` はDevConcordの文書用であり、外部の `my-app/` に対する汎用検証器ではありません。

```sh
cd ~/projects/devconcord
python3 scripts/manage_skills.py validate
python3 scripts/validate_docs.py
python3 -B -m unittest discover -s tests -v
npx --yes markdownlint-cli2@0.23.3 "**/*.md"
```

コマンド例と入力パスはこの資料の想定レイアウトに対するものです。エージェントでBootstrap/Adoption/Synchronizationを実行した品質は、静的検証やPythonテストだけでは保証されません。

## 10. よくあるエラー

| 状況 | 対処 |
|---|---|
| Bootstrapが対象を既存リポジトリと判定して止まる | `my-new-app/` が空か確認します。既存成果物や履歴を消さず、既存プロジェクトならAdoptionを使います。Skillsを先に導入していた場合はmanifest・全Skillハッシュ等を確認するか、新規で空の対象を用意してBootstrap後にSkillを導入します。 |
| CodexがDevConcordのプロンプト/設計書を読めない | CLIでパスを確認し、対象で起動したCodexへプロンプト全文を貼り付けます。必要な設計書や共通資料だけを対象に一時コピーする場合も、入力として明示し、元資料集を編集しないよう指定します。 |
| `manage_skills.py` が `local modifications detected` と報告する | 対象Skillとmanifestを保全し、対象のローカル編集を確認・退避してから再試行します。上書きを強制する目的でmanifestを書き換えたり、検査を回避したりしません。 |
| 同名Skillまたは複数探索先の重複が報告される | Skill名と各配置内容・利用agentを確認し、必要な配置だけに整理します。重複の明示許可は実エージェントでの挙動を確認した後に限ります。 |
| 通常のSkills同期が出典変更・履歴巻き戻し・比較基準エラーで止まる | ソースremote・完全SHA・履歴とmanifest記録を確認します。意図した出典変更は[運用ガイド](agent-skills.md)の `rebind-source`、中断後は `recover` を参照し、通常syncで履歴を飛ばしたり復旧データを削除したりしません。 |
| プロンプトのSynchronizationが資料別基準SHAやprovenanceを見つけられない | 初回Adoption記録の有無、各資料の比較基準と適用メモを確認します。SHAや適用状態を推測せず、不明なら作業を止めて確認します。 |
| Codex CLIコマンドが見つからない、拡張にアクセスできない | [公式Codex CLI手順](https://developers.openai.com/codex/cli)または[IDE拡張手順](https://developers.openai.com/codex/ide)で導入・サインイン・ワークスペース権限を確認します。 |
