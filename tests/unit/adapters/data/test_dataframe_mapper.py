"""
DataFrameMapper 단위 테스트
"""
import pytest
import pandas as pd
from datetime import date
from core.domain.models import StockInfo
from infra.adapters.data.dataframe_mapper import DataFrameMapper


class TestDataFrameMapper:
    """DataFrameMapper 클래스 테스트"""
    
    @pytest.fixture
    def mapper(self):
        """DataFrameMapper 인스턴스 생성"""
        return DataFrameMapper()
    
    @pytest.fixture
    def sample_stocks(self):
        """테스트용 StockInfo 리스트 생성"""
        return [
            StockInfo(
                name="테스트기업",
                url="http://test.com",
                market_segment="코스닥",
                sector="IT",
                revenue=1000,
                profit_pre_tax=100,
                net_profit=80,
                capital=500,
                total_shares=10000,
                par_value=500,
                desired_price_range="10000~12000",
                confirmed_price=11000,
                offering_amount=110000,
                underwriter="테스트증권",
                listing_date="2024-01-01",
                competition_rate="1000:1",
                emp_shares=100,
                inst_shares=5000,
                retail_shares=2000,
                tradable_shares_count="3000",
                tradable_shares_percent="30%",
            ),
            StockInfo(
                name="샘플기업",
                url="http://sample.com",
                market_segment="코스피",
                sector="제조",
                revenue=2000,
                profit_pre_tax=200,
                net_profit=160,
                capital=1000,
                total_shares=20000,
                par_value=1000,
                desired_price_range="20000~24000",
                confirmed_price=22000,
                offering_amount=440000,
                underwriter="샘플증권",
                listing_date="2024-02-01",
                competition_rate="500:1",
                emp_shares=200,
                inst_shares=10000,
                retail_shares=4000,
                tradable_shares_count="6000",
                tradable_shares_percent="30%",
            )
        ]

    def test_to_dataframe_with_data(self, mapper, sample_stocks):
        """
        데이터가 있는 경우 DataFrame으로 올바르게 변환되는지 테스트합니다.
        
        Arrange: 샘플 StockInfo 리스트 준비
        Act: to_dataframe 호출
        Assert: DataFrame의 크기, 컬럼명, 데이터 값 검증
        """
        # Act
        df = mapper.to_dataframe(sample_stocks)
        
        # Assert
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        
        # 컬럼명 확인 (매핑된 한글 컬럼명)
        expected_columns = [
            "종목명", "URL", "시장구분", "업종", "매출액(백만원)", "법인세비용차감전(백만원)",
            "순이익(백만원)", "자본금(백만원)", "총공모주식수", "액면가", "희망공모가액",
            "확정공모가", "공모금액(백만원)", "주간사", "상장일", "기관경쟁률",
            "우리사주조합", "기관투자자", "일반청약자", "유통가능물량(주)", "유통가능물량(%)"
        ]
        assert list(df.columns) == expected_columns
        
        # 데이터 값 확인
        assert df.iloc[0]["종목명"] == "테스트기업"
        assert df.iloc[0]["매출액(백만원)"] == 1000
        assert df.iloc[1]["종목명"] == "샘플기업"
        assert df.iloc[1]["확정공모가"] == 22000

    def test_to_dataframe_empty_list(self, mapper):
        """
        빈 리스트 입력 시 빈 DataFrame을 반환하는지 테스트합니다.
        
        Arrange: 빈 리스트 준비
        Act: to_dataframe 호출
        Assert: 빈 DataFrame이지만 컬럼은 존재해야 함
        """
        # Act
        df = mapper.to_dataframe([])
        
        # Assert
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        
        # 컬럼은 여전히 존재해야 함
        expected_columns = [
            "종목명", "URL", "시장구분", "업종", "매출액(백만원)", "법인세비용차감전(백만원)",
            "순이익(백만원)", "자본금(백만원)", "총공모주식수", "액면가", "희망공모가액",
            "확정공모가", "공모금액(백만원)", "주간사", "상장일", "기관경쟁률",
            "우리사주조합", "기관투자자", "일반청약자", "유통가능물량(주)", "유통가능물량(%)"
        ]
        assert list(df.columns) == expected_columns
