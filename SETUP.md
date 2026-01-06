# 🚀 TMF爆発察知ツール セットアップガイド

## 📋 クイックスタート（5分で完了）

### ステップ1: リポジトリをフォーク

1. GitHubにログイン
2. このリポジトリページで「Fork」ボタンをクリック
3. 自分のアカウントにフォーク完了

### ステップ2: Slack通知設定（オプション）

#### Slack Incoming Webhook取得

1. [Slack API](https://api.slack.com/messaging/webhooks) にアクセス
2. 「Create New App」→「From scratch」
3. アプリ名を入力（例: TMF Monitor）、ワークスペースを選択
4. 「Incoming Webhooks」を有効化
5. 「Add New Webhook to Workspace」をクリック
6. 通知先チャンネルを選択（例: #tmf-monitor）
7. Webhook URLをコピー（`https://hooks.slack.com/services/...`）

#### GitHub Secretsに登録

1. フォークしたリポジトリの「Settings」タブ
2. 左メニュー「Secrets and variables」→「Actions」
3. 「New repository secret」をクリック
4. 以下を入力：
   - **Name**: `SLACK_WEBHOOK_URL`
   - **Secret**: コピーしたWebhook URL
5. 「Add secret」をクリック

### ステップ3: GitHub Pages有効化

1. リポジトリの「Settings」タブ
2. 左メニュー「Pages」
3. 以下を設定：
   - **Source**: Deploy from a branch
   - **Branch**: `main`
   - **Folder**: `/docs`
4. 「Save」をクリック

### ステップ4: GitHub Actions実行

1. リポジトリの「Actions」タブ
2. 緑のボタン「I understand my workflows, go ahead and enable them」をクリック
3. 左サイドバー「TMF Monitor」をクリック
4. 右上「Run workflow」→「Run workflow」で手動実行
5. 実行完了まで約30秒〜1分待つ

### ステップ5: ダッシュボード確認

実行完了後、以下のURLにアクセス：

```
https://[あなたのGitHubユーザー名].github.io/[リポジトリ名]/
```

例:
```
https://john-doe.github.io/tmf-monitor/
```

## 🎉 完了！

これで毎日JST 7:00に自動実行されます。

---

## ⚙️ 詳細設定

### 実行時間のカスタマイズ

`.github/workflows/tmf.yml` を編集：

```yaml
schedule:
  # JST 7:00 (UTC 22:00)
  - cron: '0 22 * * *'
```

**よく使う時間:**
- JST 7:00 → `0 22 * * *` (UTC 22:00)
- JST 9:00 → `0 0 * * *` (UTC 0:00)
- JST 12:00 → `0 3 * * *` (UTC 3:00)
- JST 21:00 → `0 12 * * *` (UTC 12:00)

### スコア閾値のカスタマイズ

`src/scoring.py` の `THRESHOLDS` を編集：

```python
THRESHOLDS = {
    'normal': (0, 39),      # 🟢 通常
    'precursor': (40, 64),  # ⚠️ 前兆
    'alert': (65, 79),      # 🚨 警戒
    'imminent': (80, 100)   # 💥 直前
}
```

### 重み付けのカスタマイズ

`src/scoring.py` の `WEIGHTS` を編集：

```python
WEIGHTS = {
    'interest_rate': 0.40,  # 金利系: 40%
    'risk_off': 0.60        # リスクオフ系: 60%
}
```

---

## 🧪 ローカルテスト

### 環境セットアップ

```bash
# リポジトリクローン
git clone https://github.com/[username]/tmf-monitor.git
cd tmf-monitor

# 仮想環境作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存関係インストール
pip install -r requirements.txt
```

### テスト実行

```bash
# Slack通知なしで実行
cd src
python main.py

# Slack通知ありで実行
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
cd src
python main.py
```

### 生成ファイル確認

```bash
# ダッシュボード
open ../docs/index.html

# データJSON
cat ../docs/data.json
```

---

## 🐛 トラブルシューティング

### Q: Actions実行が失敗する

**A:** エラーログを確認：
1. 「Actions」タブ→失敗したワークフロー
2. 「monitor」ジョブをクリック
3. 各ステップのログを確認

**よくあるエラー:**
- データ取得エラー → FRED/Yahoo FinanceのAPI一時的ダウン
- 権限エラー → Settings→Actions→General→Workflow permissionsを「Read and write」に変更

### Q: Slack通知が届かない

**A:** チェック項目：
1. `SLACK_WEBHOOK_URL` Secretが正しく設定されているか
2. Webhook URLが有効か（ブラウザでアクセスしてテスト）
3. Actionsログで通知送信成功しているか確認

### Q: GitHub Pagesが表示されない

**A:** チェック項目：
1. Settings→Pagesで正しく設定されているか
2. `docs/index.html` が存在するか
3. Actions実行後、反映まで数分待つ
4. ブラウザのキャッシュクリア

### Q: データが古い

**A:** 以下を確認：
1. GitHub Actionsが正常に実行されているか
2. cronスケジュールが正しいか
3. 手動実行で最新データを取得

---

## 📞 サポート

問題が解決しない場合：

1. [Issues](https://github.com/username/tmf-monitor/issues) で質問
2. ログとエラーメッセージを添付
3. 実行環境（OS、Pythonバージョン）を記載

---

## 🎯 次のステップ

- [ ] Slack通知をカスタマイズ
- [ ] スコア閾値を自分好みに調整
- [ ] cron実行時間を変更
- [ ] ダッシュボードのデザインをカスタマイズ

**Happy Monitoring! 📊💥**
