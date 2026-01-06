# 💥 TMF爆発察知ツール

**TMF（20年超米国債レバレッジETF）の環境認識専用ツール**

完全無料で運用できる、GitHub Actions + Python + GitHub Pages を使ったTMF監視システムです。

## 🎯 特徴

- ✅ **完全無料**: APIキー不要、サーバー不要
- ✅ **自動実行**: GitHub Actionsで毎日JST 7:00に自動監視
- ✅ **Slack通知**: ステータス変化と定期サマリーを通知
- ✅ **視覚的ダッシュボード**: GitHub Pagesで公開
- ✅ **定量評価**: 0-100点のスコアで環境を数値化

## 📊 監視指標

### 金利系（40%）
- 米10年国債利回り
- 米30年国債利回り
- 金利の週次変化率

### リスクオフ系（60%）
- VIX指数
- S&P500終値
- S&P500の200日移動平均乖離率

## 🚦 判定ステータス

| スコア | ステータス | 意味 |
|--------|------------|------|
| 0-39 | 🟢 通常 | TMF上昇環境ではない |
| 40-64 | ⚠️ 前兆 | TMF上昇の前兆（数週間前） |
| 65-79 | 🚨 警戒 | TMF上昇の可能性が高い |
| 80-100 | 💥 直前 | TMF爆発直前（数日〜1週間前） |

## 📁 プロジェクト構成

```
tmf-monitor/
├── .github/
│   └── workflows/
│       └── tmf.yml              # GitHub Actions設定
├── src/
│   ├── main.py                  # メインスクリプト
│   ├── data_fetch.py            # データ取得
│   ├── scoring.py               # スコアリング
│   ├── notify.py                # Slack通知
│   └── render.py                # HTML生成
├── docs/                        # GitHub Pages公開ディレクトリ
│   ├── index.html               # ダッシュボード（自動生成）
│   ├── data.json                # 最新データ（自動生成）
│   └── previous.json            # 前回データ（自動生成）
├── requirements.txt             # Python依存関係
└── README.md                    # このファイル
```

## 🚀 セットアップ手順

### 1. リポジトリをフォーク

このリポジトリを自分のGitHubアカウントにフォークします。

### 2. Slack Webhook URL取得（オプション）

Slack通知を使う場合は、Incoming Webhookを設定します。

1. Slackワークスペースで [Incoming Webhooks](https://api.slack.com/messaging/webhooks) を有効化
2. 通知先チャンネルを選択
3. Webhook URLをコピー（`https://hooks.slack.com/services/...`）

### 3. GitHub Secretsを設定

リポジトリの `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

| Secret名 | 値 | 必須 |
|----------|-----|------|
| `SLACK_WEBHOOK_URL` | SlackのWebhook URL | オプション |

### 4. GitHub Pagesを有効化

1. リポジトリの `Settings` → `Pages`
2. Source: `Deploy from a branch`
3. Branch: `main` / `/docs`
4. Save

### 5. GitHub Actionsを有効化

1. リポジトリの `Actions` タブを開く
2. 「I understand my workflows, go ahead and enable them」をクリック
3. 左サイドバーから「TMF Monitor」ワークフローを選択
4. 「Run workflow」で手動実行してテスト

### 6. ダッシュボードURLを確認

実行完了後、以下のURLでダッシュボードにアクセスできます：

```
https://[あなたのGitHubユーザー名].github.io/[リポジトリ名]/
```

例: `https://username.github.io/tmf-monitor/`

## ⚙️ カスタマイズ

### 実行時間を変更

`.github/workflows/tmf.yml` の `cron` を編集：

```yaml
schedule:
  - cron: '0 22 * * *'  # UTC 22:00 = JST 7:00
```

### スコアリング基準を調整

`src/scoring.py` の `TMFScorer` クラス内の以下の値を変更：

- `WEIGHTS`: カテゴリ重み
- `BASELINE`: 基準値
- `THRESHOLDS`: ステータス閾値

## 🔍 ローカルでテスト

```bash
# 依存関係インストール
pip install -r requirements.txt

# テスト実行
cd src
python main.py
```

実行後、`docs/` ディレクトリに以下が生成されます：
- `index.html`: ダッシュボード
- `data.json`: 最新データ
- `previous.json`: 前回データ

## 📱 Slack通知の種類

### 1. ステータス変化通知

ステータスが変化した場合のみ送信：
- 通常 ⇔ 前兆
- 前兆 ⇔ 警戒
- 警戒 ⇔ 直前

### 2. 定期サマリー通知（毎日）

ステータスに関わらず毎日送信：
- TMFスコア
- 前日比
- カテゴリ別スコア
- 主なシグナル

## 📈 データソース

- **金利データ**: [FRED (Federal Reserve Economic Data)](https://fred.stlouisfed.org/)
- **VIX**: FRED経由
- **S&P500**: [Yahoo Finance](https://finance.yahoo.com/)

すべて無料APIを使用し、APIキーは不要です。

## ⚠️ 注意事項

- **このツールは環境認識専用です。売買判断は行いません。**
- スコアはあくまで参考値です。実際の投資判断は自己責任で行ってください。
- データ取得元のAPIが変更される可能性があります。
- GitHub Actionsの無料枠は月2,000分まで（通常は十分）

## 🐛 トラブルシューティング

### データ取得エラー

- FREDやYahoo FinanceのAPIが一時的にダウンしている可能性
- 数時間後に再実行してみてください

### Slack通知が届かない

1. `SLACK_WEBHOOK_URL` Secretが正しく設定されているか確認
2. Webhook URLが有効か確認（ブラウザでアクセスして確認）
3. GitHub Actionsのログを確認

### GitHub Pagesが表示されない

1. GitHub Pagesが有効になっているか確認
2. `docs/index.html` が存在するか確認
3. Actions実行後、反映まで数分かかる場合があります

## 📊 リポジトリ統計

![GitHub stars](https://img.shields.io/github/stars/username/tmf-monitor?style=social)
![GitHub forks](https://img.shields.io/github/forks/username/tmf-monitor?style=social)
![GitHub workflow status](https://img.shields.io/github/actions/workflow/status/username/tmf-monitor/tmf.yml?branch=main)

## 📄 ライセンス

MIT License

## 🤝 コントリビューション

プルリクエスト歓迎！

バグ報告や機能要望は [Issues](https://github.com/username/tmf-monitor/issues) へ。

## 📞 サポート

質問や問題がある場合は、GitHubのIssuesでお気軽にお問い合わせください。

---

**⚡ Powered by GitHub Actions + Python + GitHub Pages**
