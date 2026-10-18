# 旧プロンプトURLとAgent Skills

作業ワークフローの正本は [`.agents/skills/`](../.agents/skills/) にあるAgent Skillsです。`prompts/`の5つの旧パスは既存リンクとの互換性のため短い移行案内として残しています。旧ファイルは実行手順の全文ではありません。

| 旧プロンプトURL | 正本のSkill | 詳細手順 |
|---|---|---|
| [`bootstrap-from-design.md`](bootstrap-from-design.md) | [`bootstrap-from-design`](../.agents/skills/bootstrap-from-design/SKILL.md) | [`workflow.md`](../.agents/skills/bootstrap-from-design/references/workflow.md) |
| [`adopt-guidance.md`](adopt-guidance.md) | [`adopt-guidance`](../.agents/skills/adopt-guidance/SKILL.md) | [`workflow.md`](../.agents/skills/adopt-guidance/references/workflow.md) |
| [`sync-guidance.md`](sync-guidance.md) | [`sync-guidance`](../.agents/skills/sync-guidance/SKILL.md) | [`workflow.md`](../.agents/skills/sync-guidance/references/workflow.md) |
| [`create-agents-md.md`](create-agents-md.md) | [`generate-agent-guidance`](../.agents/skills/generate-agent-guidance/SKILL.md) | [`agents-md.md`](../.agents/skills/generate-agent-guidance/references/agents-md.md) |
| [`create-reviews-md.md`](create-reviews-md.md) | [`generate-agent-guidance`](../.agents/skills/generate-agent-guidance/SKILL.md) | [`reviews-md.md`](../.agents/skills/generate-agent-guidance/references/reviews-md.md) |

## 使い方

Skills対応エージェントでは、対象リポジトリを作業コンテキストにして適切なSkillを選択します。作業場所・入力・安全条件・検証は[実行例付きの導入ガイド](../docs/getting-started.md)を参照してください。Agent Skillsの導入・同期・復旧は[運用ガイド](../docs/agent-skills.md)が正本です。

Skills非対応環境では、表にあるSkillの `SKILL.md` と必要な詳細手順を読み、その両方の全文を対象エージェントへ渡してください。AGENTS/REVIEWS生成では実行モードに応じたreferenceを選びます。旧URLの案内だけを渡しても作業ワークフロー全文にはなりません。SkillがローカルDevConcord資料を必要とする場合は、Skill内の `references/local-devconcord.md` に従い、実際に読めた場合だけ参照済みと扱います。

## Agent Skills

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

Skillsの自動発見・選択はエージェントや実行環境によって異なり、常に保証されるものではありません。実行確認と静的検証の証拠は区別してください。
