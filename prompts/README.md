# 指示ファイル生成プロンプト

対象リポジトリを調査し、実際の構成・技術・テスト・CI・既存規約に基づいて指示ファイルを作るためのプロンプトです。

| プロンプト | 出力先 | 用途 |
|---|---|---|
| [AGENTS.md 生成](create-agents-md.md) | 対象リポジトリの `AGENTS.md` | 日常の開発作業で常時守るリポジトリ固有ルール |
| [REVIEWS.md 生成](create-reviews-md.md) | 対象リポジトリの `REVIEWS.md` | コードレビュー時に確認する固有の契約・リスク |
| [設計書から新規リポジトリを初期化](bootstrap-from-design.md) | 新規プロジェクトの基盤・設計/運用資料・必要な最小骨格 | 設計要求から開発可能・検証可能なリポジトリを構築 |
| [既存プロジェクトへの初回導入](adopt-guidance.md) | 対象リポジトリの必要な資料・指示ファイル | 既存資料を調べ、必要な共通ルールを選んで統合 |
| [導入済み資料の更新](sync-guidance.md) | 対象リポジトリの採用済み資料 | 資料別の比較基準コミット以降の差分と保留メモを照合し、必要な変更だけを適用 |

## 使い方

対象リポジトリの作業コンテキストで、使うプロンプトの全文をAIエージェントへ渡します。`<...>` の箇所は対象に合わせて置き換えてください。新規リポジトリを設計書から作る場合はBootstrap、すでに存在するプロジェクトへ共通資料を適用する場合は初回導入、導入済み資料を更新する場合は同期を使います。Bootstrapは既存成果物のあるディレクトリを新規扱いで上書きする用途ではありません。各作業後は根拠のない記述や既存ルールとの重複・矛盾を人が確認します。設計原則の適用はプロジェクト規模に合わせ、UI/UXを機能設計へ、Performance / Robustnessを必要な要求・契約・検証へ、Replaceabilityを交換価値のある依存境界へつなぎます。特にCLIやライブラリへGUI要件を課さず、別の課題・リスク台帳や全依存の抽象化も無条件に追加しません。具体的な準備・操作は[はじめての導入と運用](../docs/getting-started.md)を参照してください。

このリポジトリにある共通ガイドやテンプレートを適用する場合は、対象リポジトリへ必要な資料をコピーし、そのパスをプロンプトに明示してください。`AGENTS.md` にはレビュー時に `REVIEWS.md` を読む手順を含め、任意のファイルが自動読込される前提にしないでください。

## Agent Skills

作業単位の再利用可能なSkillは [`.agents/skills/`](../.agents/skills/) に標準形式の正本を置きます。導入先に応じてOpenAI Codex / GitHub Copilotは `.agents/skills/`、Claude Codeは `.claude/skills/` を選びます。外部リポジトリへは [`manage_skills.py`](../scripts/manage_skills.py) で選択導入・同期できます。`install` / `sync` は `--apply` がなければdry-runで、既存Skillの編集・同名衝突を上書きせず保護します。配置方法、重複探索の回避、記録形式は[導入ガイド](../docs/getting-started.md#agent-skillsを利用する)を参照してください。

CodexとCopilotは `.agents/skills/` を共同利用でき、Claude CodeとCopilotは `.claude/skills/` を共同利用できます。CodexとClaude Codeは別々の探索先へ配置します。三者併用時はCopilotの同名重複解決が未検証のため、確認後に限り `--allow-duplicate-discovery` を明示してください。Claude Code用の配置は正本からの生成コピーで、シンボリックリンクを前提にしません。コピーを直接編集せず、Skill更新ツールで差分を確認してください。

manifest schema 2は配置先ごとに共有agentとSkill provenanceを保存します。旧schema 1は読み込み時に保護的に移行し、未知・破損形式は変更しません。通常同期は同一コミットまたは祖先からの前進のみを許可し、意図した出典変更・巻き戻しは `rebind-source` で明示します。中断更新は `recover` で調査・回復できます。どちらもdry-runで計画を確認してから適用し、異常時は不明な状態を自動破棄しません。コマンドと制限は[導入ガイド](../docs/getting-started.md#agent-skillsを利用する)を参照してください。

| Skill | 用途 |
|---|---|
| [`bootstrap-from-design`](../.agents/skills/bootstrap-from-design/SKILL.md) | 設計要求から新規リポジトリのFoundation/Scaffold/Initial Implementationを構築 |
| [`adopt-guidance`](../.agents/skills/adopt-guidance/SKILL.md) | 既存プロジェクトへ共通資料を選択導入 |
| [`sync-guidance`](../.agents/skills/sync-guidance/SKILL.md) | 導入済み資料・Skillsをローカル変更を保護しながら同期 |
| [`ux-functional-design`](../.agents/skills/ux-functional-design/SKILL.md) | ユーザー目標を機能・状態・受け入れ条件へ接続 |
| [`design-performance`](../.agents/skills/design-performance/SKILL.md) | ワークロードに基づく性能設計と測定条件を定義 |
| [`design-robustness`](../.agents/skills/design-robustness/SKILL.md) | 不変条件・失敗時契約・回復・検証を設計 |
| [`design-replaceability`](../.agents/skills/design-replaceability/SKILL.md) | 交換価値と抽象化コストに基づき依存境界を設計 |
| [`repository-review`](../.agents/skills/repository-review/SKILL.md) | 実装・設計・テスト・CI・運用記録を根拠にレビュー |
| [`generate-agent-guidance`](../.agents/skills/generate-agent-guidance/SKILL.md) | 実態に基づく `AGENTS.md` と `REVIEWS.md` の作成・更新 |

Skills対応エージェントでは適切なSkillが自動発見・選択されることがありますが、常に発見や呼び出しが保証されるわけではありません。既存プロンプトは互換性のある手動実行入口として維持し、Skills非対応環境では従来どおり全文を渡して実行してください。Agent Skills導入は各ベンダーの実機評価とは区別します。
