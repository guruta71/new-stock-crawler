"""
CrawlerService 통합 테스트
새로운 아키텍처가 제대로 동작하는지 검증
"""
import pytest
from unittest.mock import Mock, MagicMock
from datetime import date

from core.services.crawler_service import CrawlerService
from core.domain.models import ScrapeReport, StockInfo


class TestCrawlerService:
    """CrawlerService 통합 테스트"""
    
    @pytest.fixture
    def mock_dependencies(self):
        """모든 의존성 모킹"""
        return {
            'page_provider': Mock(),
            'calendar_scraper': Mock(),
            'detail_scraper': Mock(),
            'data_mapper': Mock(),
            'data_exporter': Mock(),
            'date_calculator': Mock(),
            'logger': Mock()
        }
    
    @pytest.fixture
    def crawler_service(self, mock_dependencies):
        """CrawlerService 인스턴스 생성"""
        return CrawlerService(**mock_dependencies)
    
    def test_service_initialization(self, crawler_service, mock_dependencies):
        """서비스가 모든 의존성을 제대로 주입받는지 확인"""
        assert crawler_service.page_provider == mock_dependencies['page_provider']
        assert crawler_service.calendar_scraper == mock_dependencies['calendar_scraper']
        assert crawler_service.detail_scraper == mock_dependencies['detail_scraper']
        assert crawler_service.data_mapper == mock_dependencies['data_mapper']
        assert crawler_service.data_exporter == mock_dependencies['data_exporter']
        assert crawler_service.date_calculator == mock_dependencies['date_calculator']
        assert crawler_service.logger == mock_dependencies['logger']
    
    def test_run_with_single_year(self, crawler_service, mock_dependencies):
        """단일 연도 크롤링이 제대로 동작하는지 확인"""
        # Given: 날짜 계산기가 2024년 범위를 반환
        mock_date_range = Mock(start_month=1, end_month=12, day_limit=31)
        mock_dependencies['date_calculator'].calculate.return_value = {
            2024: mock_date_range
        }
        
        # Given: Page 객체 모킹
        mock_page = Mock()
        mock_dependencies['page_provider'].get_page.return_value = mock_page
        
        # Given: 캘린더 스크래퍼가 종목 반환
        stock_tuple = ("테스트종목", "http://example.com")
        mock_report = ScrapeReport(
            final_stock_count=1,
            spack_filtered_count=0,
            results=[stock_tuple]
        )
        mock_dependencies['calendar_scraper'].scrape_calendar.return_value = mock_report
        
        # Given: 상세 스크래퍼가 StockInfo 반환
        mock_stock = StockInfo(
            name="테스트종목",
            url="http://example.com",
            market_segment="KOSPI",
            sector="IT",
            revenue=1000,
            profit_pre_tax=100,
            net_profit=80,
            capital=500,
            total_shares=1000000,
            par_value=500,
            desired_price_range="10000-12000",
            confirmed_price=11000,
            offering_amount=11000000000,
            underwriter="테스트증권",
            listing_date="2024-12-01",
            competition_rate="100:1",
            emp_shares=10000,
            inst_shares=50000,
            retail_shares=40000,
            tradable_shares_count="900000",
            tradable_shares_percent="90%"
        )
        mock_dependencies['detail_scraper'].scrape_details.return_value = [mock_stock]
        
        # Given: 데이터 매퍼가 DataFrame 반환
        import pandas as pd
        mock_df = pd.DataFrame([{
            'name': '테스트종목',
            'market': 'KOSPI'
        }])
        mock_dependencies['data_mapper'].to_dataframe.return_value = mock_df
        
        # When: 크롤링 실행
        crawler_service.run(start_year=2024)
        
        # Then: 각 컴포넌트가 올바르게 호출되었는지 확인
        mock_dependencies['date_calculator'].calculate.assert_called_once()
        mock_dependencies['page_provider'].get_page.assert_called_once()
        mock_dependencies['calendar_scraper'].scrape_calendar.assert_called_once_with(
            page=mock_page,
            year=2024,
            start_month=1,
            end_month=12,
            today_day=31
        )
        mock_dependencies['detail_scraper'].scrape_details.assert_called_once_with(
            page=mock_page,
            stocks=[stock_tuple]
        )
        mock_dependencies['data_mapper'].to_dataframe.assert_called_once()
        mock_dependencies['data_exporter'].export.assert_called_once()
    
    def test_run_with_no_results(self, crawler_service, mock_dependencies):
        """결과가 없을 때 저장하지 않는지 확인"""
        # Given: 빈 결과 반환
        mock_date_range = Mock(start_month=1, end_month=12, day_limit=31)
        mock_dependencies['date_calculator'].calculate.return_value = {
            2024: mock_date_range
        }
        
        mock_page = Mock()
        mock_dependencies['page_provider'].get_page.return_value = mock_page
        
        # 빈 리포트
        empty_report = ScrapeReport(
            final_stock_count=0,
            spack_filtered_count=5,
            results=[]
        )
        mock_dependencies['calendar_scraper'].scrape_calendar.return_value = empty_report
        
        # When: 크롤링 실행
        crawler_service.run(start_year=2024)
        
        # Then: export가 호출되지 않아야 함
        mock_dependencies['data_exporter'].export.assert_not_called()
        mock_dependencies['logger'].warning.assert_called()
    
    def test_run_with_multiple_years(self, crawler_service, mock_dependencies):
        """여러 연도 크롤링이 제대로 동작하는지 확인"""
        # Given: 2023, 2024년 범위 반환
        mock_dependencies['date_calculator'].calculate.return_value = {
            2023: Mock(start_month=1, end_month=12, day_limit=31),
            2024: Mock(start_month=1, end_month=11, day_limit=26)
        }
        
        mock_page = Mock()
        mock_dependencies['page_provider'].get_page.return_value = mock_page
        
        # 각 연도마다 결과 반환
        mock_dependencies['calendar_scraper'].scrape_calendar.return_value = ScrapeReport(
            final_stock_count=1,
            spack_filtered_count=0,
            results=[("종목", "http://test.com")]
        )
        
        mock_dependencies['detail_scraper'].scrape_details.return_value = [
            Mock(spec=StockInfo)
        ]
        
        import pandas as pd
        mock_dependencies['data_mapper'].to_dataframe.return_value = pd.DataFrame([{'name': 'test'}])
        
        # When: 크롤링 실행
        crawler_service.run(start_year=2023)
        
        # Then: calendar_scraper가 2번 호출되어야 함
        assert mock_dependencies['calendar_scraper'].scrape_calendar.call_count == 2
        assert mock_dependencies['detail_scraper'].scrape_details.call_count == 2
        mock_dependencies['data_exporter'].export.assert_called_once()
