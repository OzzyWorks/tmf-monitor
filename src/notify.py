"""
Slack通知モジュール
Incoming Webhookを使用してSlackに通知
"""

import os
import requests
from datetime import datetime


class SlackNotifier:
    """Slack Incoming Webhookで通知するクラス"""
    
    def __init__(self, webhook_url=None):
        """
        Args:
            webhook_url: Slack Incoming Webhook URL (指定なしの場合は環境変数から取得)
        """
        self.webhook_url = webhook_url or os.environ.get('SLACK_WEBHOOK_URL')
        
        if not self.webhook_url:
            print("⚠️  SLACK_WEBHOOK_URL が設定されていません")
            self.enabled = False
        else:
            self.enabled = True
    
    def send_status_change_notification(self, current_result, previous_result, dashboard_url):
        """
        ステータス変化通知を送信
        
        Args:
            current_result: 現在のスコアリング結果
            previous_result: 前回のスコアリング結果
            dashboard_url: ダッシュボードURL
        """
        if not self.enabled:
            print("⚠️  Slack通知がスキップされました（Webhook未設定）")
            return False
        
        current_status = current_result['status']['level']
        previous_status = previous_result['status']['level'] if previous_result else 'unknown'
        
        # ステータスが変化していない場合はスキップ
        if current_status == previous_status and previous_result is not None:
            print("ℹ️  ステータス変化なし（通知スキップ）")
            return False
        
        # メッセージ作成
        message = self._build_status_change_message(
            current_result, 
            previous_result, 
            dashboard_url
        )
        
        # 送信
        return self._send_to_slack(message)
    
    def send_daily_summary(self, result, previous_result, dashboard_url):
        """
        定期サマリー通知を送信（毎日）
        
        Args:
            result: スコアリング結果
            previous_result: 前回のスコアリング結果
            dashboard_url: ダッシュボードURL
        """
        if not self.enabled:
            print("⚠️  Slack通知がスキップされました（Webhook未設定）")
            return False
        
        # メッセージ作成
        message = self._build_daily_summary_message(
            result, 
            previous_result, 
            dashboard_url
        )
        
        # 送信
        return self._send_to_slack(message)
    
    def _build_status_change_message(self, current, previous, dashboard_url):
        """ステータス変化通知メッセージを構築"""
        status = current['status']
        score = current['total_score']
        
        # 前回スコア
        previous_score = previous['total_score'] if previous else 0
        score_diff = score - previous_score
        
        # 変化方向
        if score_diff > 0:
            trend = "📈 上昇"
            trend_emoji = "⚠️"
        elif score_diff < 0:
            trend = "📉 低下"
            trend_emoji = "✅"
        else:
            trend = "→ 変化なし"
            trend_emoji = "ℹ️"
        
        # 前回ステータス
        prev_status_text = ""
        if previous:
            prev_status_text = f"{previous['status']['emoji']} {previous['status']['label']}"
        else:
            prev_status_text = "（初回実行）"
        
        # ブロック形式のメッセージ
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{trend_emoji} TMFステータス変化検知",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*現在のステータス*\n{status['emoji']} *{status['label']}*"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*TMFスコア*\n*{score}点* ({score_diff:+.1f})"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*前回ステータス*\n{prev_status_text}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*変化*\n{trend}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*主なシグナル*\n" + "\n".join([f"• {s}" for s in current['signals'][:3]])
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<{dashboard_url}|📊 ダッシュボードを見る>"
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"更新日時: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    }
                ]
            }
        ]
        
        return {"blocks": blocks}
    
    def _build_daily_summary_message(self, result, previous, dashboard_url):
        """定期サマリーメッセージを構築"""
        status = result['status']
        score = result['total_score']
        
        # 前日比
        previous_score = previous['total_score'] if previous else score
        score_diff = score - previous_score
        
        if score_diff > 0:
            trend_text = f"📈 +{score_diff:.1f}"
        elif score_diff < 0:
            trend_text = f"📉 {score_diff:.1f}"
        else:
            trend_text = "→ 変化なし"
        
        # カテゴリ別スコア
        interest = result['category_scores']['interest_rate']['total']
        risk = result['category_scores']['risk_off']['total']
        
        # ブースト条件
        boost_text = ""
        if result['boost_conditions']['boost_applied']:
            boost_text = "\n⚡ " + "、".join(result['boost_conditions']['conditions'])
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "📊 TMF監視 - 定期レポート",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*ステータス*\n{status['emoji']} *{status['label']}*"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*TMFスコア*\n*{score}点*"
                    }
                ]
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*前日比*\n{trend_text}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*日付*\n{datetime.now().strftime('%Y-%m-%d')}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*カテゴリ別スコア*\n• 金利系: {interest:.1f}点\n• リスクオフ: {risk:.1f}点{boost_text}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*シグナル要因*\n" + "\n".join([f"• {s}" for s in result['signals'][:4]])
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<{dashboard_url}|📊 詳細ダッシュボード>"
                }
            }
        ]
        
        return {"blocks": blocks}
    
    def _send_to_slack(self, message):
        """Slackにメッセージを送信"""
        if not self.enabled:
            return False
        
        try:
            response = requests.post(
                self.webhook_url,
                json=message,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            
            print("✅ Slack通知送信成功")
            return True
            
        except Exception as e:
            print(f"❌ Slack通知送信失敗: {str(e)}")
            return False


# テスト用
if __name__ == "__main__":
    # ダミーデータでテスト
    test_result = {
        'total_score': 72.5,
        'status': {
            'level': 'alert',
            'label': '警戒',
            'emoji': '🚨',
            'color': '#ef4444'
        },
        'category_scores': {
            'interest_rate': {'total': 68.3},
            'risk_off': {'total': 75.2}
        },
        'boost_conditions': {
            'boost_applied': True,
            'boost_multiplier': 1.15,
            'conditions': ['金利2週連続急低下']
        },
        'signals': [
            '10年債低水準 (3.2%)',
            '金利急低下 (-0.8%)',
            'VIX上昇 (22.5)'
        ]
    }
    
    previous_result = {
        'total_score': 58.2,
        'status': {
            'level': 'precursor',
            'label': '前兆',
            'emoji': '⚠️',
            'color': '#f59e0b'
        }
    }
    
    notifier = SlackNotifier()
    
    if notifier.enabled:
        print("\n=== ステータス変化通知テスト ===")
        notifier.send_status_change_notification(
            test_result, 
            previous_result,
            "https://your-username.github.io/tmf-monitor/"
        )
        
        print("\n=== 定期サマリー通知テスト ===")
        notifier.send_daily_summary(
            test_result,
            previous_result,
            "https://your-username.github.io/tmf-monitor/"
        )
    else:
        print("\n環境変数 SLACK_WEBHOOK_URL を設定してください")
