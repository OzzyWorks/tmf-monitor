"""
スコアリングモジュール
取得したデータをTMFスコア（0-100）に変換
"""

import math


class TMFScorer:
    """TMF爆発スコアを計算するクラス"""
    
    # スコアリング重み
    WEIGHTS = {
        'interest_rate': 0.40,  # 金利系: 40%
        'risk_off': 0.60        # リスクオフ系: 60%
    }
    
    # 金利系の内訳
    INTEREST_WEIGHTS = {
        'treasury_10y': 0.35,
        'treasury_30y': 0.35,
        'rate_decline': 0.30
    }
    
    # リスクオフ系の内訳
    RISK_WEIGHTS = {
        'vix': 0.50,
        'sp500_deviation': 0.50
    }
    
    # スコア閾値
    THRESHOLDS = {
        'normal': (0, 39),
        'precursor': (40, 64),
        'alert': (65, 79),
        'imminent': (80, 100)
    }
    
    # 基準値（中央値的な想定）
    BASELINE = {
        'treasury_10y': 4.0,    # 10年債: 4%を基準
        'treasury_30y': 4.5,    # 30年債: 4.5%を基準
        'vix': 15.0,            # VIX: 15を基準
        'rate_decline_2w': -0.3 # 2週間で-0.3%以上の低下でハイスコア
    }
    
    def __init__(self):
        pass
    
    def calculate_score(self, data):
        """
        TMFスコアを計算
        
        Args:
            data: DataFetcherから取得したデータ
        
        Returns:
            dict: スコア詳細
        """
        indicators = data['indicators']
        
        # 各カテゴリのスコア計算
        interest_score = self._calculate_interest_score(indicators)
        risk_score = self._calculate_risk_score(indicators)
        
        # 総合スコア
        total_score = (
            interest_score['total'] * self.WEIGHTS['interest_rate'] +
            risk_score['total'] * self.WEIGHTS['risk_off']
        )
        
        # 補助条件チェック
        boost_conditions = self._check_boost_conditions(indicators)
        
        # ブースト適用
        if boost_conditions['boost_applied']:
            total_score = min(100, total_score * boost_conditions['boost_multiplier'])
        
        # ステータス判定
        status = self._determine_status(total_score)
        
        # シグナル要因を特定
        signals = self._identify_signals(indicators, interest_score, risk_score)
        
        return {
            'total_score': round(total_score, 1),
            'status': status,
            'category_scores': {
                'interest_rate': interest_score,
                'risk_off': risk_score
            },
            'boost_conditions': boost_conditions,
            'signals': signals,
            'raw_data': indicators
        }
    
    def _calculate_interest_score(self, indicators):
        """金利系スコアを計算"""
        scores = {}
        
        # 10年債スコア（低いほど高スコア）
        if indicators['treasury_10y'] is not None:
            t10y = indicators['treasury_10y']
            # 2% 以下で100点、6%以上で0点
            score = max(0, min(100, (6.0 - t10y) / 4.0 * 100))
            scores['treasury_10y'] = {
                'value': t10y,
                'score': round(score, 1)
            }
        else:
            scores['treasury_10y'] = {'value': None, 'score': 0}
        
        # 30年債スコア（低いほど高スコア）
        if indicators['treasury_30y'] is not None:
            t30y = indicators['treasury_30y']
            # 2.5% 以下で100点、6.5%以上で0点
            score = max(0, min(100, (6.5 - t30y) / 4.0 * 100))
            scores['treasury_30y'] = {
                'value': t30y,
                'score': round(score, 1)
            }
        else:
            scores['treasury_30y'] = {'value': None, 'score': 0}
        
        # 金利下落率スコア（急低下でハイスコア）
        if indicators['treasury_10y_change'] is not None:
            change = indicators['treasury_10y_change']
            change_pct = change['change_pct']
            # -1.0%以下で100点、+0.5%以上で0点
            if change_pct <= -1.0:
                score = 100
            elif change_pct >= 0.5:
                score = 0
            else:
                score = max(0, min(100, (-change_pct / 1.5) * 100))
            
            scores['rate_decline'] = {
                'value': change_pct,
                'score': round(score, 1)
            }
        else:
            scores['rate_decline'] = {'value': None, 'score': 0}
        
        # 総合スコア
        total = (
            scores['treasury_10y']['score'] * self.INTEREST_WEIGHTS['treasury_10y'] +
            scores['treasury_30y']['score'] * self.INTEREST_WEIGHTS['treasury_30y'] +
            scores['rate_decline']['score'] * self.INTEREST_WEIGHTS['rate_decline']
        )
        
        return {
            'total': round(total, 1),
            'details': scores
        }
    
    def _calculate_risk_score(self, indicators):
        """リスクオフスコアを計算"""
        scores = {}
        
        # VIXスコア（高いほど高スコア）
        if indicators['vix'] is not None:
            vix = indicators['vix']
            # 10以下で0点、30以上で100点
            score = max(0, min(100, (vix - 10) / 20 * 100))
            scores['vix'] = {
                'value': vix,
                'score': round(score, 1)
            }
        else:
            scores['vix'] = {'value': None, 'score': 0}
        
        # S&P500乖離率スコア（マイナス乖離で高スコア）
        if indicators['sp500'] is not None:
            sp = indicators['sp500']
            deviation = sp['deviation_pct']
            # -10%以下で100点、+5%以上で0点
            if deviation <= -10:
                score = 100
            elif deviation >= 5:
                score = 0
            else:
                score = max(0, min(100, (-deviation / 15) * 100))
            
            scores['sp500_deviation'] = {
                'value': deviation,
                'price': sp['price'],
                'ma_200': sp['ma_200'],
                'score': round(score, 1)
            }
        else:
            scores['sp500_deviation'] = {'value': None, 'score': 0}
        
        # 総合スコア
        total = (
            scores['vix']['score'] * self.RISK_WEIGHTS['vix'] +
            scores['sp500_deviation']['score'] * self.RISK_WEIGHTS['sp500_deviation']
        )
        
        return {
            'total': round(total, 1),
            'details': scores
        }
    
    def _check_boost_conditions(self, indicators):
        """補助条件（ブースト）をチェック"""
        conditions = []
        boost_multiplier = 1.0
        
        # 条件1: 金利が2週連続で急低下
        if indicators['treasury_10y_change'] is not None:
            change = indicators['treasury_10y_change']
            if change['change_pct'] <= -0.5:
                conditions.append('金利2週連続急低下')
                boost_multiplier = max(boost_multiplier, 1.15)
        
        # 条件2: VIX上昇 + S&P500が200DMA割れ
        vix_high = indicators['vix'] is not None and indicators['vix'] > 20
        sp_below_ma = (
            indicators['sp500'] is not None and 
            indicators['sp500']['deviation_pct'] < -2
        )
        
        if vix_high and sp_below_ma:
            conditions.append('VIX高騰 + S&P500急落')
            boost_multiplier = max(boost_multiplier, 1.20)
        
        return {
            'boost_applied': len(conditions) > 0,
            'boost_multiplier': boost_multiplier,
            'conditions': conditions
        }
    
    def _determine_status(self, score):
        """スコアからステータスを判定"""
        if score <= self.THRESHOLDS['normal'][1]:
            return {
                'level': 'normal',
                'label': '通常',
                'emoji': '🟢',
                'color': '#10b981'
            }
        elif score <= self.THRESHOLDS['precursor'][1]:
            return {
                'level': 'precursor',
                'label': '前兆',
                'emoji': '⚠️',
                'color': '#f59e0b'
            }
        elif score <= self.THRESHOLDS['alert'][1]:
            return {
                'level': 'alert',
                'label': '警戒',
                'emoji': '🚨',
                'color': '#ef4444'
            }
        else:
            return {
                'level': 'imminent',
                'label': '直前',
                'emoji': '💥',
                'color': '#dc2626'
            }
    
    def _identify_signals(self, indicators, interest_score, risk_score):
        """主要シグナル要因を特定"""
        signals = []
        
        # 金利系シグナル
        if interest_score['details']['treasury_10y']['score'] > 60:
            signals.append(f"10年債低水準 ({interest_score['details']['treasury_10y']['value']}%)")
        
        if interest_score['details']['rate_decline']['score'] > 60:
            signals.append(f"金利急低下 ({interest_score['details']['rate_decline']['value']}%)")
        
        # リスクオフ系シグナル
        if risk_score['details']['vix']['score'] > 60:
            signals.append(f"VIX上昇 ({risk_score['details']['vix']['value']})")
        
        if risk_score['details']['sp500_deviation']['score'] > 60:
            signals.append(f"S&P500急落 ({risk_score['details']['sp500_deviation']['value']}%)")
        
        if not signals:
            signals.append("目立った変化なし")
        
        return signals


# テスト用
if __name__ == "__main__":
    # ダミーデータでテスト
    test_data = {
        'timestamp': '2024-01-01T00:00:00',
        'date': '2024-01-01',
        'indicators': {
            'treasury_10y': 3.8,
            'treasury_30y': 4.2,
            'vix': 18.5,
            'sp500': {
                'price': 4700,
                'ma_200': 4500,
                'deviation_pct': 4.4
            },
            'treasury_10y_change': {
                'current': 3.8,
                'past': 4.1,
                'change_pct': -7.3,
                'weeks': 2
            }
        }
    }
    
    scorer = TMFScorer()
    result = scorer.calculate_score(test_data)
    
    print("\n=== TMFスコア計算結果 ===")
    print(f"総合スコア: {result['total_score']}")
    print(f"ステータス: {result['status']['emoji']} {result['status']['label']}")
    print(f"\n金利系スコア: {result['category_scores']['interest_rate']['total']}")
    print(f"リスクオフスコア: {result['category_scores']['risk_off']['total']}")
    print(f"\nシグナル要因:")
    for signal in result['signals']:
        print(f"  - {signal}")
