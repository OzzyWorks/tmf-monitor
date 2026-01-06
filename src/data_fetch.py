"""
データ取得モジュール
FRED (米連邦準備銀行) とYahoo FinanceからTMF関連指標を取得
"""

import requests
from datetime import datetime, timedelta
import time


class DataFetcher:
    """無料APIからデータを取得するクラス"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'TMF-Monitor/1.0'
        })
    
    def fetch_all_data(self):
        """全ての必要なデータを取得"""
        print("📊 データ取得を開始...")
        
        data = {
            'timestamp': datetime.now().isoformat(),
            'date': datetime.now().strftime('%Y-%m-%d'),
            'indicators': {}
        }
        
        # 金利データ取得（FRED API - 無料、APIキー不要）
        try:
            data['indicators']['treasury_10y'] = self._fetch_fred_data('DGS10')
            print("✅ 10年国債利回り取得完了")
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️  10年国債利回り取得失敗: {e}")
            data['indicators']['treasury_10y'] = None
        
        try:
            data['indicators']['treasury_30y'] = self._fetch_fred_data('DGS30')
            print("✅ 30年国債利回り取得完了")
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️  30年国債利回り取得失敗: {e}")
            data['indicators']['treasury_30y'] = None
        
        # VIXデータ取得（FRED）
        try:
            data['indicators']['vix'] = self._fetch_fred_data('VIXCLS')
            print("✅ VIX取得完了")
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️  VIX取得失敗: {e}")
            data['indicators']['vix'] = None
        
        # S&P500データ取得（Yahoo Finance - スクレイピング）
        try:
            sp500_data = self._fetch_yahoo_sp500()
            data['indicators']['sp500'] = sp500_data
            print("✅ S&P500取得完了")
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️  S&P500取得失敗: {e}")
            data['indicators']['sp500'] = None
        
        # 金利の変化率を計算
        try:
            data['indicators']['treasury_10y_change'] = self._calculate_rate_change('DGS10')
            print("✅ 10年債変化率計算完了")
            time.sleep(0.5)
        except Exception as e:
            print(f"⚠️  10年債変化率計算失敗: {e}")
            data['indicators']['treasury_10y_change'] = None
        
        print("✅ 全データ取得完了\n")
        return data
    
    def _fetch_fred_data(self, series_id, days_back=1):
        """
        FREDからデータを取得（APIキー不要の公開エンドポイント使用）
        
        Args:
            series_id: FREDのシリーズID
            days_back: 何日前までのデータを取得するか
        
        Returns:
            float: 最新の値
        """
        # FREDの公開データエンドポイント（CSVフォーマット）
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back * 2)  # 余裕を持って取得
        
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # CSVをパース（最終行が最新データ）
            lines = response.text.strip().split('\n')
            if len(lines) < 2:
                raise ValueError(f"No data returned for {series_id}")
            
            # 最終行から値を取得
            for line in reversed(lines[1:]):  # ヘッダーをスキップ
                parts = line.split(',')
                if len(parts) >= 2 and parts[1] != '.' and parts[1] != '':
                    value = float(parts[1])
                    return value
            
            raise ValueError(f"No valid data found for {series_id}")
            
        except Exception as e:
            raise Exception(f"FRED API error for {series_id}: {str(e)}")
    
    def _fetch_yahoo_sp500(self):
        """
        Yahoo FinanceからS&P500のデータを取得
        
        Returns:
            dict: 現在値、200日移動平均、乖離率
        """
        symbol = "^GSPC"  # S&P500のシンボル
        
        # Yahoo Finance Chart API（公開エンドポイント）
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {
            'interval': '1d',
            'range': '1y'  # 200日移動平均計算用に1年分取得
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # データ抽出
            result = data['chart']['result'][0]
            closes = result['indicators']['quote'][0]['close']
            
            # None値を除外
            valid_closes = [c for c in closes if c is not None]
            
            if len(valid_closes) < 200:
                raise ValueError("Not enough data for 200-day MA calculation")
            
            current_price = valid_closes[-1]
            ma_200 = sum(valid_closes[-200:]) / 200
            deviation = ((current_price - ma_200) / ma_200) * 100
            
            return {
                'price': round(current_price, 2),
                'ma_200': round(ma_200, 2),
                'deviation_pct': round(deviation, 2)
            }
            
        except Exception as e:
            raise Exception(f"Yahoo Finance API error: {str(e)}")
    
    def _calculate_rate_change(self, series_id, weeks=2):
        """
        金利の変化率を計算（週次）
        
        Args:
            series_id: FREDのシリーズID
            weeks: 何週間前と比較するか
        
        Returns:
            dict: 現在値、過去値、変化率
        """
        try:
            # 現在値
            current = self._fetch_fred_data(series_id, days_back=1)
            
            # 週次データなので営業日を考慮
            days_back = weeks * 7 + 5  # 余裕を持って取得
            
            # 過去データ取得
            url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            lines = response.text.strip().split('\n')
            
            # 日付でソート済みなので最新から遡る
            valid_data = []
            for line in reversed(lines[1:]):
                parts = line.split(',')
                if len(parts) >= 2 and parts[1] != '.' and parts[1] != '':
                    valid_data.append({
                        'date': parts[0],
                        'value': float(parts[1])
                    })
            
            if len(valid_data) < weeks * 5:  # 週5営業日
                raise ValueError("Not enough historical data")
            
            # 週次で比較
            past_value = valid_data[weeks * 5]['value']
            change_rate = ((current - past_value) / past_value) * 100
            
            return {
                'current': round(current, 3),
                'past': round(past_value, 3),
                'change_pct': round(change_rate, 2),
                'weeks': weeks
            }
            
        except Exception as e:
            raise Exception(f"Rate change calculation error: {str(e)}")


# テスト用
if __name__ == "__main__":
    fetcher = DataFetcher()
    data = fetcher.fetch_all_data()
    
    print("\n=== 取得データ ===")
    print(f"取得日時: {data['timestamp']}")
    print(f"\n10年債利回り: {data['indicators']['treasury_10y']}%")
    print(f"30年債利回り: {data['indicators']['treasury_30y']}%")
    print(f"VIX: {data['indicators']['vix']}")
    
    if data['indicators']['sp500']:
        sp = data['indicators']['sp500']
        print(f"\nS&P500: {sp['price']}")
        print(f"200日移動平均: {sp['ma_200']}")
        print(f"乖離率: {sp['deviation_pct']}%")
    
    if data['indicators']['treasury_10y_change']:
        change = data['indicators']['treasury_10y_change']
        print(f"\n10年債変化率: {change['change_pct']}% ({change['weeks']}週間)")
