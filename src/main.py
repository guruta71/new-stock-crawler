# src/main.py
"""
Stock Crawler Main Application
새로운 아키텍처 기반 (Clean Architecture + Hexagonal)
"""
from datetime import date

# Core
from core.services.crawler_service import CrawlerService

# Adapters - Web Scraping
from infra.adapters.web.playwright_page_provider import PlaywrightPageProvider
from infra.adapters.web.calendar_scraper_adapter import CalendarScraperAdapter
from infra.adapters.web.detail_scraper_adapter import DetailScraperAdapter

# Adapters - Data
from infra.adapters.data.dataframe_mapper import DataFrameMapper
from infra.adapters.excel_persistence_adapter import LocalExcelPersistenceAdapter

# Adapters - Utilities
from infra.adapters.utils.console_logger import ConsoleLogger
from infra.adapters.utils.date_calculator import DateRangeCalculator


def main():
    """메인 애플리케이션 진입점"""
    
    # 설정
    START_YEAR = 2020
    HEADLESS = True
    
    # ========================================
    # 의존성 생성 (Dependency Injection)
    # ========================================
    
    # 1. 유틸리티
    logger = ConsoleLogger()
    date_calculator = DateRangeCalculator()
    
    # 2. Web Scraping
    page_provider = PlaywrightPageProvider(headless=HEADLESS)
    calendar_scraper = CalendarScraperAdapter()
    detail_scraper = DetailScraperAdapter()
    
    # 3. Data
    data_mapper = DataFrameMapper()
    data_exporter = LocalExcelPersistenceAdapter()
    
    # 4. Service (모든 의존성 주입)
    crawler_service = CrawlerService(
        page_provider=page_provider,
        calendar_scraper=calendar_scraper,
        detail_scraper=detail_scraper,
        data_mapper=data_mapper,
        data_exporter=data_exporter,
        date_calculator=date_calculator,
        logger=logger
    )
    
    # ========================================
    # 크롤링 실행
    # ========================================
    
    try:
        logger.info("=" * 60)
        logger.info("🚀 Stock Crawler 시작")
        logger.info(f"📅 기준 날짜: {date.today()}")
        logger.info(f"📆 크롤링 시작 연도: {START_YEAR}년")
        logger.info("🔍 필터: (상장) 포함, 스팩 제외")
        logger.info("=" * 60)
        
        # Playwright 초기화
        page_provider.setup()
        
        # CrawlerService가 모든 비즈니스 로직을 처리
        crawler_service.run(start_year=START_YEAR)
        
        logger.info("=" * 60)
        logger.info("🏁 모든 크롤링 작업 완료")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.warning("\n⚠️  사용자에 의해 중단되었습니다")
    except Exception as e:
        logger.error(f"❌ 크롤링 중 오류 발생: {e}")
        raise
    finally:
        # 리소스 정리
        page_provider.cleanup()
        logger.info("\n✅ 리소스 정리 완료")


if __name__ == "__main__":
    main()