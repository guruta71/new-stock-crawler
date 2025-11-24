import time
from typing import List, Tuple
from playwright.sync_api import Browser, Page, Playwright, sync_playwright

from domain.ports import IPOInfoPort
from domain.models import ScrapeReport, StockInfo

# 분리된 파서 클래스들을 임포트합니다.
from infra.adapters.parsers.calander_parser import CalendarParser
from infra.adapters.parsers.detail_parser import StockDetailParser


class PlaywrightIPOAdapter(IPOInfoPort):
    BASE_URL: str = "https://www.38.co.kr"
    SCHEDULE_URL: str = f"{BASE_URL}/html/ipo/ipo_schedule.php"

    def __init__(self, headless: bool = True) -> None:
        self.headless: bool = headless
        self.playwright: Playwright | None = None
        self.browser: Browser | None = None
        self.page: Page | None = None
        
        # 파서 인스턴스를 저장할 변수
        self.calendar_parser: CalendarParser | None = None
        self.detail_parser: StockDetailParser | None = None
        
        print(f"Playwright 어댑터 초기화 (Headless: {self.headless})")

    def setup(self) -> None:
        """Initialize Playwright browser, page, and parsers."""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page()
            
            # 페이지 객체가 생성된 후 파서들을 초기화하고 페이지를 주입합니다.
            self.calendar_parser = CalendarParser(self.page, self.BASE_URL, self.SCHEDULE_URL)
            self.detail_parser = StockDetailParser(self.page)
            
            print("Playwright 브라우저 및 파서가 성공적으로 시작되었습니다.")
        except Exception as e:
            print(f"Playwright 브라우저 시작 중 오류 발생: {e}")
            print("   [팁] 'playwright install' 명령어를 실행했는지 확인하세요.")
            raise

    def cleanup(self) -> None:
        """Close browser and cleanup resources."""
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
            print("Playwright 브라우저가 종료되었습니다.")
        if self.playwright:
            self.playwright.stop()

    def get_ipos_for_period(
        self, year: int, start_month: int, end_month: int, today_day: int
    ) -> ScrapeReport:
        """
        Scrape IPO listings for the specified period.
        (Delegates to CalendarParser)
        """
        if not self.calendar_parser:
            raise RuntimeError("Adapter is not set up. 'setup()' must be called first.")
        
        print(f"--- 'get_ipos_for_period' (Adapter) 실행 -> CalendarParser에 위임 ---")
        return self.calendar_parser.get_ipos(
            year, start_month, end_month, today_day
        )

    def scrape_stock_details(self, stocks: List[Tuple[str, str]]) -> List[StockInfo]:
        """
        Scrape detailed information for multiple stocks.
        (Delegates to StockDetailParser)
        """
        if not self.detail_parser:
            raise RuntimeError("Adapter is not set up. 'setup()' must be called first.")
        
        print(f"--- 'scrape_stock_details' (Adapter) 실행 -> DetailParser에 위임 ---")
        return self.detail_parser.scrape_details(stocks)

    def test_navigation(self, year: int, start_month: int, end_month: int) -> None:
        """
        Test navigation through monthly pages.
        (Delegates to CalendarParser)
        """
        if not self.calendar_parser:
            raise RuntimeError("Adapter is not set up. 'setup()' must be called first.")
            
        print(f"--- 'test_navigation' (Adapter) 실행 -> CalendarParser에 위임 ---")
        self.calendar_parser.test_navigation(year, start_month, end_month)