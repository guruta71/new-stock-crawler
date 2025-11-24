# src/infra/adapters/dataframe_adapter.py
import pandas as pd
from typing import List
from domain.models import StockInfo

def convert_to_dataframe(stocks: List[StockInfo]) -> pd.DataFrame:
    """
    List[StockInfo] 객체를 이미지 형식의 DataFrame으로 변환합니다.
    """
    
    # 1. 이미지에 표시된 19개 열 이름을 정확하게 정의합니다.
    columns = [
        "종목명", "구분", "업종", "매출액", "법인세비용차감전순이익", "순이익",
        "자본금", "총공모주식수", "액면가", "희망공모가", "확정공모가", "공모금액",
        "주간사", "기관투자자", "일반투자자", "우리사주조합", "기관경쟁률", "상장일",
        "유통가능물량(주식수)", "유통가능물량(지분율)"
    ]

    # 2. List[StockInfo]가 비어있다면, 열(column)만 있는 빈 DataFrame을 반환합니다.
    if not stocks:
        return pd.DataFrame(columns=columns)

    # 3. StockInfo 객체를 순회하며 DataFrame의 행(row) 데이터(data)를 만듭니다.
    data = []
    for stock in stocks:
        data.append([
            stock.name,
            stock.market_segment,
            stock.sector,
            stock.revenue,
            stock.profit_pre_tax,
            stock.net_profit,
            stock.capital,
            stock.total_shares,
            stock.par_value,
            stock.desired_price_range,
            stock.confirmed_price,
            stock.offering_amount,
            stock.underwriter,
            stock.inst_shares,
            stock.retail_shares,
            stock.emp_shares,
            stock.competition_rate,
            stock.listing_date,
            stock.tradable_shares_count,
            stock.tradable_shares_percent
        ])

    # 4. 데이터와 컬럼을 사용하여 DataFrame을 생성합니다.
    df = pd.DataFrame(data, columns=columns)
    
    return df