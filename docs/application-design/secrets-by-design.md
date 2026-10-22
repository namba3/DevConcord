# Secrets by Design

本ガイドは、Security by Designの下で、秘密情報を必要な範囲に限定し、資格情報の発行から失効までを設計するための詳細資料です。「Secrets by Design」はDevConcord内の整理名であり、外部規格への準拠や安全性の認証を意味しません。すべての製品に秘密情報基盤やクラウドIDを導入する規則でもありません。対象の利用者、実行環境、脅威、運用能力に応じて必要な判断だけを行います。

## 適用範囲と用語

パスワード、APIキー、アクセストークン、リフレッシュトークン、証明書秘密鍵、データ暗号鍵など、漏えい・悪用により資産や操作へ影響する値を扱います。秘密情報が存在しない、または新たな秘密情報を導入しない小さな変更では、その判断を短く記録すれば十分です。暗号鍵は認証資格情報と用途・ライフサイクルが異なるため、鍵の生成、保管、利用、バックアップ、ローテーション、失効、破棄は必要に応じて別契約として扱います。

| 用語 | 意味 |
|---|---|
| 主体 (principal) | 人、プロセス、ワークロード、サービスなど、要求を行う識別対象 |
| 認証 (authentication) | 主体の識別・証明 |
| 認可 (authorization) | 認証された主体が対象の操作を行えるかの判定。認証成功だけでは認可を意味しない |
| ブートストラップ信頼 | 最初のID・資格情報・信頼アンカーを、どの主体/基盤がどのように与えるか |
| Workload Identity | 実行中のワークロードに結び付いた識別。IDの取得後も、対象側の認可設定が必要 |
| 短期資格情報 | 有効期限の短い資格情報。Bearer token等は期限内に盗まれれば再利用され得る |
| Secretless | アプリケーションが長期秘密の配布・保管・更新を必要としないようにする設計戦略。基盤や実行プロセスに秘密が一切ないという保証ではない |

侵害された正規プロセスが許可済み操作を行うリスクは、資格情報をSecret Managerへ移すだけでは除去できません。認可範囲、実行分離、対象制限、監査、失敗時の動作も脅威に応じて扱います。

## 設計原則

- **Secret Minimization:** 共有埋め込みキー、リポジトリや成果物に含む資格情報、用途のない永続トークンを避けます。提供元がID連携をサポートするか、サーバー側処理・ユーザー認証・限定プロキシで秘密の配布先を減らせるかを先に調べます。Secretless Architectureは、この必要性そのものを減らす主要戦略です。
- **Identity First / Least Privilege:** 発行者、主体、対象、audience、用途、操作、資源、テナント、環境、時間を必要な範囲に限定します。IDを得た主体にも、対象システム側の認可を設定します。
- **Temporal Minimization / Lifecycle Automation:** 有効期間、更新可能期間、キャッシュ、接続プール、失効伝播を含めて露出時間を扱います。生成・発行・更新・ローテーション・失効・廃棄の自動化は、提供元と運用が安全に支えられる範囲で行います。根拠のない固定TTL・ローテーション間隔は決めません。
- **Bootstrap Trust:** IDプロバイダーやSecret Managerへ接続する最初の信頼を特定し、それが過剰な静的資格情報へ再帰していないか確認します。人による初期プロビジョニング、OS/クラウド実行基盤ID、デバイス鍵、信頼済みissuer等は環境別の候補です。
- **Exposure Containment / Observability:** 資格情報をソース、設定例、ログ、エラー、テレメトリ、スクリーンショット、テスト成果物へ出しません。必要な監査には主体ID、対象、操作、判定、相関ID、発行/更新/失効結果などのメタデータを記録し、秘密値や復元可能な断片を記録しません。
- **Replaceability:** 認証方式や提供元の将来変更が現実的な場合、意味のあるポートと契約を設けます。単一実装のAPI形状をそのまま包むだけの抽象を強制しません。

## 選択肢の比較

選択肢は単一の優先順位ではありません。提供元が要求する主体、実行環境、オフライン動作、利用者操作、失効要件、障害時の可用性、運用可能性から比較します。Workload Identity Federationと動的資格情報は解決する境界が異なり、組み合わせる場合もあります。

| 方式 | 主な用途・利点 | 主な残余リスク・確認事項 |
|---|---|---|
| Workload Identity / Managed Identity | 対応基盤が実行中の主体を識別し、アプリが長期クラウド資格情報を保持しない | 基盤のID割当・分離、メタデータ/APIへのアクセス範囲、対象側IAM認可、同一ホスト上の他ワークロードからの隔離を確認 |
| Federation / STS | OIDC等の外部IDを限定条件で検証し、対象向け短期資格情報へ交換 | issuer、audience、subject/claim、環境・ref等を厳密に束縛。issuer侵害、誤ったclaim条件、token replay、交換先権限を確認 |
| 動的資格情報 / 短期リース | DBユーザー等をオンデマンド発行し、期限・失効を自動管理 | 発行基盤自体のブートストラップ、更新障害、リース失効、接続プール内の古い資格情報、発行権限を確認 |
| Secret Manager + 静的資格情報 | 提供元がID連携を持たない場合の保管・配布・監査・更新 | 取得主体の資格情報、平文利用時のプロセス露出、キャッシュ/複製/バックアップ、ローテーションの適用漏れは残る |
| OS資格情報ストア / 保護されたサービスcredential | デスクトップ利用者やOSサービスで、ユーザー/サービス境界に沿った保存・配布 | OSアカウント、ACL、バックアップ、端末侵害、アンロック/ログイン条件、利用時のプロセス露出を確認 |
| ファイルまたは環境変数 | 小規模・既存運用・互換性上必要な場合の単純な受け渡し | どちらも自動的に安全ではない。ファイルはACL、所有者、バックアップ、配布・更新を、環境変数は継承先、診断、ダンプ、プロセス起動系の露出を比較し、脅威とOSに合う方を選ぶ |
| Broker / Proxy | 固定キー専用APIをサーバー側に隠し、許可した操作だけを仲介 | BrokerがConfused Deputyや高価値侵害点になる。呼出元認証、資源/操作allowlist、テナント境界、レート制限、監査、障害・濫用を確認 |

Secret Managerは秘密の保管・配布を改善しますが、利用時にアプリが受け取る平文や、侵害済みプロセスの権限行使はなくしません。環境変数とファイルも一律に順位付けせず、権限境界、継承、ダンプ、OSの保護機能、運用手順を比べます。短期Bearer tokenも秘密として扱い、期限切れまで再利用できる可能性を評価します。

## パターンと境界

### Workload IdentityとFederation

クラウド実行基盤、CI、Kubernetes、SPIFFE等が提供するIDを利用する場合、ID発行元から対象サービスまでの信頼関係を定義します。Federationではissuer、audience、subject、および利用できる追加claimを対象リポジトリ・環境・ref・ワークロードへ必要な粒度で束縛します。tokenを取得できる権限だけを絞っても、信頼ポリシーの広さや交換後の認可が適切とは限りません。

ブートストラップ信頼には、実行基盤のメタデータID、署名済みCI ID token、端末/ハードウェアID、管理者が導入する初期鍵などがあり得ます。どの方式も、その発行主体・鍵・claim検証・侵害時影響を明示します。Workload IdentityやSPIFFE/SPIREを全製品へ要求せず、既存基盤と変更価値で判断します。JWT形式のID assertionは構成によってreplayの性質が異なるため、有効期間、audience、署名鍵ローテーション、再利用防止を当該プロトコルの仕様で確認します。

SPIFFE IDはTrust Domain内でワークロードを表すURI形式の識別子です。SPIFFE Workload APIは、ワークロードのattestation後にX.509-SVID（証明書と秘密鍵）やJWT-SVIDを配布する例を定義します。Trust Domainは信頼するID発行範囲を示し、SVIDはその範囲内のID証明です。X.509-SVIDとJWT-SVIDは配布・検証・replay等の特性が異なるため、プロトコルと相手側対応に合わせて選びます。SPIFFE/SPIRE自体を採用する場合は、attestation条件、Trust Domainの運用、Workload API socketへのアクセス制御、SVID更新時の接続再確立まで含めて評価します。

### 動的資格情報と接続プール

リース期限と更新/失効は、依存する処理の寿命と合わせて扱います。期限切れ、発行元停止、権限変更時に新規処理を拒否するか、既存接続をどこまで維持するかを定義します。資格情報を更新しても既存DB接続が古い主体・権限を維持する場合があるため、プールの排出・再接続、進行中処理、部分成功を含む契約を決めます。更新を並行して重複実行しない方法、バックオフ、ジッター、失敗時の利用者/運用者向け診断も必要性に応じて設計します。

資格情報取得の遅延やissuerへの負荷が重要なら、cold startと通常運転の取得時間、キャッシュの有効範囲・失効反映、更新集中時の競合、接続プール再作成を実際のワークロードで測ります。キャッシュは可用性・性能を改善し得ますが、失効遅延や古い権限を保持するため、その上限を脅威・可用性契約から決めます。

### Broker、Proxy、暗号操作サービス

Broker/Proxyは長期キーの配布先を減らせますが、権限を集約します。呼出元IDから許可対象・操作への対応をサーバー側で強制し、呼出元が任意の宛先・テナント・キーIDを選べないようにします。Brokerが侵害・誤設定されたときの到達範囲、依存障害、濫用、監査、緊急停止方法を評価します。

KMS/HSM等の非エクスポート鍵は、鍵素材の取得を防いでも、許可された署名・復号APIの悪用は防ぎません。鍵管理権限、鍵利用権限、操作対象の認可を区別し、暗号鍵の生成・ローテーション・復旧・破棄を認証資格情報のライフサイクルと混同しません。

## ライフサイクルと障害時の契約

以下の用語を区別します。

| 操作 | 契約 |
|---|---|
| Expiration | 有効期限到達により資格情報が自動的に無効になること |
| Refresh | 現在の資格情報等を使い、期限前後に新しい資格情報を取得すること。Refresh Token自体が長期秘密の場合がある |
| Rotation | 発行側で資格情報を置換し、利用側へ安全に切り替えること。旧新資格情報の重複期間、適用確認、ロールバックを定義 |
| Revocation | 期限前に利用権を無効化すること。伝播遅延、キャッシュ、進行中接続、失効確認を扱う |
| Reauthentication | 主体が再度認証・証明を行うこと。refreshやrotationと同義ではない |

資格情報取得・更新・失効の失敗は、セキュリティと可用性を同時に変えます。期限切れ時に不許可操作を継続しない不変条件、既に認可済みの処理を続行できる時間、オフライン利用、キャッシュ上限、停止後の再開を要求として必要な範囲で定義します。失敗のたびに権限を広げたり、未知の資格情報へ無条件にfallbackしたりしません。安全なフェイルクローズが可用性要件と衝突する場合は、限定された処理、既存接続、利用者通知など許容範囲を明示し、残余リスクを記録します。

## 実行環境ごとの代表的判断

| 環境 | 判断例 |
|---|---|
| クラウドワークロード | 基盤ID/短期トークン、リソースごとのIAM、実行単位の分離、metadata endpoint到達範囲 |
| Kubernetes | SecretのRBAC・at-rest暗号化・マウント方法、ServiceAccount tokenのaudience/期限、外部ID連携。Kubernetes SecretのBase64表現を暗号化とみなさない |
| CI/CD | OIDC federationを使えるか、issuer/audience/subject条件をbranch/tag/environment等へ限定するか、workflowの変更権限とid-token権限 |
| Linuxサービス | systemd credentials、サービスアカウント、ファイルACL、資格情報更新とプロセス再読込の契約。OS固有機能の有無を確認 |
| Windows/Linuxデスクトップ | 共通APIキーをバイナリへ埋め込まない。対応サービスではブラウザ経由のAuthorization Code + PKCE等の公開クライアント向けフロー、ユーザーごとの認可、OS資格情報ストアを検討 |
| オフラインアプリ | 常時接続のSecret Managerを前提にしない。OS/ハードウェア保護、ローカル暗号鍵の回復不能性、同期時の最小権限を要件化 |
| 固定キー専用の旧式API | サーバー仲介や提供元への移行を評価し、残す場合はキーの範囲・保管・配布・ローテーション・監視・漏えい対応を定義 |

デスクトップ公開クライアントに埋め込んだ共有クライアントシークレットは、利用者が抽出できるものとして扱います。OAuth/OIDCを使う場合、対象サービス・フローに対応する現行RFCやプロバイダー仕様を選び、PKCE、redirect URI、state、audience、ユーザー認可、refresh token保護など適用範囲を確認します。PKCE等はフローの脅威を軽減しますが、端末侵害やユーザー資格情報の保護を代替しません。

## 受け入れ条件と検証

対象に関連する条件を選び、要求、実装・設定、実行された検証、残余リスクを区別します。

- ソース、生成物、ログ、診断、テスト結果、サンプルへ実資格情報を含めず、リポジトリのサンプル値は明示的なダミー値だけを使う。
- 認証成功と認可成功を分け、誤った主体・issuer・audience・subject・tenant・資源・操作は拒否される。
- 期限切れ、更新、失効、発行元停止、並行更新、ローテーションの切替・ロールバック、古い接続プールを含む関連状態を検証する。
- Broker/Proxyが許可外の呼出元・宛先・tenant・操作を拒否し、濫用と監査情報を扱う。
- 鍵素材をエクスポートできない条件だけでなく、未許可の暗号操作が拒否されることも確認する。
- OS/クラウド/CI設定を含む環境依存の制御は、その環境で確認する。モックやユニットテストだけではIAM、issuer条件、ACL、Secret Manager設定の証拠にならない。

秘密スキャナーは検出対象・設定・除外に限った補助証拠であり、秘密が存在しないことや使用時の安全性を証明しません。テスト fixtureには実資格情報や本番形式の利用可能なtokenを入れません。失敗経路を実行していない場合、テストがあるだけで検証済みと報告しません。

要求仕様では、該当する場合に秘密の必要性、主体・認証・認可、ブートストラップ、権限・時間範囲、失敗時の契約、検証方法を既存のREQ/NFRへ結び付けます。重要な方式選択は既存ADRへ記録し、残余リスク・作業は既存のリスク記録・課題表を使います。新しい品質評価軸や資格情報専用台帳を作りません。

## 参考資料

以下は設計判断の出発点です。仕様・サービス機能は更新され得るため、採用時に対象バージョンと環境の一次資料を確認してください。

- [OWASP Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)：保管、利用、ローテーション、動的資格情報と露出面。
- [HashiCorp Vault leases](https://developer.hashicorp.com/vault/docs/concepts/lease)：リース、更新、失効の実装例。プロバイダーとleaseable backendの挙動を確認する。
- [CISA Secure by Design](https://www.cisa.gov/securebydesign)：製品提供者の設計原則。Secrets by Designという本ガイド内の整理名を規格として定義する資料ではない。
- [RFC 9700: Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700.html) と [RFC 8252: OAuth 2.0 for Native Apps](https://www.rfc-editor.org/rfc/rfc8252.html)：OAuthの脅威緩和とネイティブアプリ。
- [RFC 9449: OAuth 2.0 Demonstrating Proof of Possession (DPoP)](https://www.rfc-editor.org/rfc/rfc9449.html)：対応する場合のsender-constrained token。全方式への一律要求ではない。
- [SPIFFE Concepts](https://spiffe.io/docs/latest/spiffe/concepts/) と [Workload API](https://spiffe.io/docs/latest/spiffe-specs/spiffe_workload_api/)：ワークロードIDとSVIDの例。
- [Kubernetes Secrets good practices](https://kubernetes.io/docs/concepts/security/secrets-good-practices/) と [Service Accounts](https://kubernetes.io/docs/concepts/security/service-accounts/)：Kubernetes固有のアクセス・トークン設定。
- [systemd.exec credentials](https://www.freedesktop.org/software/systemd/man/latest/systemd.exec.html) と [system credentials](https://www.freedesktop.org/software/systemd/man/latest/systemd.system-credentials.html)：Linux/systemd固有の配布方法。
- [GitHub Actions OIDC](https://docs.github.com/en/actions/reference/security/oidc)、[Google Workload Identity Federation](https://cloud.google.com/iam/docs/workload-identity-federation)、[AWS temporary credentials](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_temp.html)、[Azure managed identities](https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/overview)：各基盤の連携例。設定値・信頼条件を各公式資料で確認する。
- [Windows Credential Locker](https://learn.microsoft.com/en-us/windows/apps/develop/security/credential-locker) と [GNOME libsecret](https://gnome.pages.gitlab.gnome.org/libsecret/)：デスクトップOS固有の保存手段。
- [AWS KMS data protection](https://docs.aws.amazon.com/kms/latest/developerguide/data-protection.html)：特定のKMSにおける鍵素材とAPI操作の例。
