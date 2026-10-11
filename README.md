# ソフトウェア開発プロジェクト運用資料

このリポジトリは、ソフトウェア開発プロジェクトの計画・設計・実装・レビュー・リリースを運用するための共通資料、テンプレート、AI向けプロンプトを管理します。

## ディレクトリ

- [`docs/`](docs/README.md): 共通設計原則・開発/レビュー規約、要求・リスク・課題表管理、完成度評価と各種テンプレート
- [`prompts/`](prompts/README.md): `AGENTS.md`・`REVIEWS.md` の生成、既存プロジェクトへの初回導入、導入済み資料の差分同期に使うプロンプト

## 使い方

導入手順、Codex CLI・VS Codeでの使い方、導入後チェック、資料版の記録方法は[はじめての導入と運用](docs/getting-started.md)を参照してください。

ガイドとテンプレートは[資料一覧](docs/README.md)、初回導入・更新や指示ファイル生成に使うプロンプトは[プロンプト一覧](prompts/README.md)から選べます。

共通資料にはDDD・TDD・DbC・Self-documenting Code・Doc Comments・Annotation Comments・Performance by Design等の原則と、開発・レビュー・品質管理の規約があります。要求仕様とリスクを追跡し、課題表方式の作業管理、SDS、既存10軸の完成度評価を支援します。資料の一覧と選び方は[docs/README.md](docs/README.md)を参照してください。

資料は初期値です。対象プロジェクトに既存のルールや管理方法がある場合は、それを確認してから適用してください。プロンプトの選択や導入手順は[prompts/README.md](prompts/README.md)と[導入ガイド](docs/getting-started.md)を参照してください。

共通開発原則では、DDDで概念と責務の正しさを、Self-documenting Codeで理解可能性を、Performance by Designで処理構造の効率性を重視します。個人・秘密・環境情報を保護し、契約や要求への適合と重要な性能特性は独立した検証で確認します。詳しくは[資料一覧](docs/README.md)からAI支援開発ガイドと課題管理規約を参照してください。
