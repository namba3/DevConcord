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

プロンプトは導入先リポジトリを作業コンテキストとして実行し、DevConcordを読み取り専用の参照元として指定します。`<...>` の箇所は対象に合わせて置き換えてください。新規リポジトリを設計書から作る場合はBootstrap、すでに存在するプロジェクトへ共通資料を適用する場合はAdoption、導入済み資料を更新する場合は資料Synchronizationを使います。Bootstrapは既存成果物のあるディレクトリを新規扱いで上書きする用途ではありません。各作業後は根拠のない記述や既存ルールとの重複・矛盾を人が確認します。設計原則の適用はプロジェクト規模に合わせ、UI/UXを機能設計へ、Performance / Robustnessを必要な要求・契約・検証へ、Replaceabilityを交換価値のある依存境界へつなぎます。特にCLIやライブラリへGUI要件を課さず、別の課題・リスク台帳や全依存の抽象化も無条件に追加しません。具体的な準備・操作は[実行例付きの導入ガイド](../docs/getting-started.md)を参照してください。

プロンプトの実行とAgent Skills管理CLIは別の操作です。Skillsは通常User Scopeとしてユーザー環境へ一度導入します。Project Scopeが必要な場合だけ `--scope project --target <導入先>` を指定します。`install` / `sync` はdry-runが既定で、差分を確認してから `--apply` を使います。共通資料のSynchronizationはプロンプトによる文書差分適用であり、`manage_skills.py sync` はmanifest管理下のSkillsパッケージ同期です。Skillのコマンド・出典・復旧手順は[Agent Skills運用ガイド](../docs/agent-skills.md)を参照してください。

このリポジトリにある共通ガイドやテンプレートを適用する場合は、対象リポジトリへ必要な資料をコピーし、そのパスをプロンプトに明示してください。`AGENTS.md` にはレビュー時に `REVIEWS.md` を読む手順を含め、任意のファイルが自動読込される前提にしないでください。

## Agent Skills

作業単位の再利用可能なSkillは [`.agents/skills/`](../.agents/skills/) に標準形式の正本を置きます。Skill一覧から目的に合うワークフローを選び、通常はユーザー環境へUser Scopeとして導入します。チーム共有・CI・バージョン固定ではProject Scopeを選べます。導入・同期・復旧は[Agent Skills運用ガイド](../docs/agent-skills.md)を参照してください。CLIはDevConcordのローカル参照先とSkillの出典コミットを用いて、必要な資料を同じ版から読み出せます。エージェントがローカルファイルへアクセスできない場合は、その環境で参照済みと扱いません。

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
| [`documentation-architecture`](../.agents/skills/documentation-architecture/SKILL.md) | 読者タスクを中心にREADME・文書構造・導線・保守性をレビュー・改善 |

Skills対応エージェントでは適切なSkillが自動発見・選択されることがありますが、常に発見や呼び出しが保証されるわけではありません。既存プロンプトは互換性のある手動実行入口として維持し、Skills非対応環境では従来どおり全文を渡して実行してください。Agent Skills導入は各ベンダーの実機評価とは区別します。
