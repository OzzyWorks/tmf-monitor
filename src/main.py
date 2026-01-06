"""
メインスクリプト
全モジュールを統合してTMF監視を実行
"""

import os
import sys
import json
from datetime import datetime

# モジュールをインポート
from data_fetch import DataFetcher
from scoring import TMFScorer
from notify import SlackNotifier
from render import DashboardRenderer


class TMFMonitor:
    """TMF監視メインクラス"""
    
    def __init__(self, docs_dir='docs'):
        self.docs_dir = docs_dir
        self.data_json_path = os.path.join(docs_dir, 'data.json')
        self.previous_data_path = os.path.join(docs_dir, 'previous.json')
        self.index_html_path = os.path.join(docs_dir, 'index.html')
        
        # GitHub PagesのベースURL（環境変数から取得、なければデフォルト）
        repo_name = os.environ.get('GITHUB_REPOSITORY', 'username/tmf-monitor')
        self.dashboard_url = f"https://{repo_name.split('/')[0]}.github.io/{repo_name.split('/')[1]}/"
        
        # 各モジュールを初期化
        self.fetcher = DataFetcher()
        self.scorer = TMFScorer()
        self.notifier = SlackNotifier()
        self.renderer = DashboardRenderer()
    
    def load_previous_result(self):
        """前回実行結果を読み込み"""
        if not os.path.exists(self.previous_data_path):
            print("ℹ️  前回データなし（初回実行）")
            return None
        
        try:
            with open(self.previous_data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print("✅ 前回データ読み込み完了")
                return data
        except Exception as e:
            print(f"⚠️  前回データ読み込み失敗: {e}")
            return None
    
    def save_current_as_previous(self, result):
        """現在の結果を前回データとして保存"""
        try:
            with open(self.previous_data_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print("✅ 前回データとして保存")
        except Exception as e:
            print(f"⚠️  前回データ保存失敗: {e}")
    
    def run(self):
        """メイン処理を実行"""
        print("=" * 60)
        print("🚀 TMF爆発察知ツール 実行開始")
        print(f"実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        print()
        
        # ステップ1: データ取得
        print("【ステップ1】データ取得")
        print("-" * 60)
        try:
            raw_data = self.fetcher.fetch_all_data()
        except Exception as e:
            print(f"❌ データ取得失敗: {e}")
            sys.exit(1)
        
        print()
        
        # ステップ2: スコアリング
        print("【ステップ2】スコアリング")
        print("-" * 60)
        try:
            result = self.scorer.calculate_score(raw_data)
            
            print(f"✅ TMFスコア: {result['total_score']}")
            print(f"✅ ステータス: {result['status']['emoji']} {result['status']['label']}")
            print(f"✅ 金利系: {result['category_scores']['interest_rate']['total']}")
            print(f"✅ リスクオフ: {result['category_scores']['risk_off']['total']}")
            
            if result['boost_conditions']['boost_applied']:
                print(f"⚡ ブースト発動: {', '.join(result['boost_conditions']['conditions'])}")
        
        except Exception as e:
            print(f"❌ スコアリング失敗: {e}")
            sys.exit(1)
        
        print()
        
        # ステップ3: 前回データと比較
        print("【ステップ3】前回データと比較")
        print("-" * 60)
        previous_result = self.load_previous_result()
        
        if previous_result:
            prev_score = previous_result['total_score']
            curr_score = result['total_score']
            diff = curr_score - prev_score
            
            print(f"前回スコア: {prev_score}")
            print(f"今回スコア: {curr_score}")
            print(f"変化: {diff:+.1f}")
            
            prev_status = previous_result['status']['label']
            curr_status = result['status']['label']
            
            if prev_status != curr_status:
                print(f"⚠️  ステータス変化検知: {prev_status} → {curr_status}")
            else:
                print(f"ℹ️  ステータス変化なし: {curr_status}")
        
        print()
        
        # ステップ4: Slack通知
        print("【ステップ4】Slack通知")
        print("-" * 60)
        
        # ステータス変化通知
        status_changed = self.notifier.send_status_change_notification(
            result, 
            previous_result, 
            self.dashboard_url
        )
        
        # 定期サマリー通知（毎日）
        summary_sent = self.notifier.send_daily_summary(
            result,
            previous_result,
            self.dashboard_url
        )
        
        print()
        
        # ステップ5: ファイル出力
        print("【ステップ5】ファイル出力")
        print("-" * 60)
        
        try:
            # docsディレクトリ作成
            os.makedirs(self.docs_dir, exist_ok=True)
            
            # data.json生成
            self.renderer.save_data_json(result, self.data_json_path)
            
            # index.html生成
            self.renderer.generate_dashboard_html(self.index_html_path)
            
            # 前回データとして保存
            self.save_current_as_previous(result)
            
        except Exception as e:
            print(f"❌ ファイル出力失敗: {e}")
            sys.exit(1)
        
        print()
        
        # 実行サマリー
        print("=" * 60)
        print("✅ TMF監視実行完了")
        print("=" * 60)
        print()
        print("📊 実行サマリー")
        print(f"  TMFスコア: {result['total_score']}")
        print(f"  ステータス: {result['status']['emoji']} {result['status']['label']}")
        print(f"  ダッシュボード: {self.dashboard_url}")
        print()
        print("主なシグナル:")
        for signal in result['signals'][:3]:
            print(f"  • {signal}")
        print()
        
        return result


def main():
    """エントリーポイント"""
    try:
        # カレントディレクトリからの相対パスでdocsを指定
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        docs_dir = os.path.join(project_root, 'docs')
        
        monitor = TMFMonitor(docs_dir=docs_dir)
        result = monitor.run()
        
        sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  実行が中断されました")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 予期しないエラー: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
