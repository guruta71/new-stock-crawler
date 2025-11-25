import time
import re
from typing import Generator, Tuple, List, Optional
from playwright.sync_api import Page, Locator

from core.domain.models import ScrapeReport
from infra.adapters.parsers import utils  # 분리된 유틸리티 함수 임포트

class CalendarParser:
    
    def __init__(self, page: Page, base_url: str, schedule_url: str):
        self.page = page
        self.BASE_URL = base_url
        self.SCHEDULE_URL = schedule_url
        print("CalendarParser (1차 파서) 초기화됨")

    def get_ipos(
        self, year: int, start_month: int, end_month: int, today_day: int
    ) -> ScrapeReport:
        """Scrape IPO listings for the specified period."""
        print(f"--- 'get_ipos' (CalendarParser) 실행 ---")
        
        total_spacks_filtered = 0
        total_results = []

        for page, month in self._visit_monthly_pages_sequentially(year, start_month, end_month):
            is_current_month = month == end_month
            print(f"      -> ({month}월) 캘린더 테이블 파싱 시작...")
            
            spack_count, results = self._parse_calendar_table(
                page, month, today_day, is_current_month
            )
            
            total_spacks_filtered += spack_count
            total_results.extend(results)
        
        print("--- 'get_ipos' (파싱) 완료 ---")
        
        return ScrapeReport(
            final_stock_count=len(total_results),
            spack_filtered_count=total_spacks_filtered,
            results=total_results
        )

    def _visit_single_month_page(self, year: int, month: int) -> Page | None:
        """Visit IPO schedule page for a specific month."""
        if not self.page:
            print(f"      [{month}월] [오류] self.page가 초기화되지 않았습니다.")
            return None
        
        month_str = f"{month:02d}"
        url = f"{self.SCHEDULE_URL}?mode=goMonth&o=s&month={month_str}&year={year}"
        
        try:
            self.page.goto(url)
            self.page.wait_for_load_state("networkidle")
            return self.page
        except Exception as e:
            print(f"      [{month}월] [오류] 페이지({url}) 방문 실패: {e}")
            return None

    def _visit_monthly_pages_sequentially(
        self, year: int, start_month: int, end_month: int
    ) -> Generator[Tuple[Page, int], None, None]:
        """Generate pages for each month in the specified range."""
        for month in range(start_month, end_month + 1):
            if page := self._visit_single_month_page(year, month):
                yield page, month

    def test_navigation(self, year: int, start_month: int, end_month: int) -> None:
        """Test navigation through monthly pages."""
        for page, month in self._visit_monthly_pages_sequentially(year, start_month, end_month):
            print(f"   -> {month}월 페이지 방문 테스트 완료")
            time.sleep(1)

    def _extract_day_from_cell(self, cell: Locator) -> Optional[int]:
        """Extract day number from calendar cell."""
        day_locator = cell.locator("table tr:first-child td:first-child b").first
        if not day_locator.is_visible():
            return None
        
        try:
            return int(day_locator.inner_text().strip())
        except ValueError:
            return None

    def _should_skip_cell(
        self, day: int, current_month: int, today_day: int, is_current_month: bool
    ) -> bool:
        """Determine if calendar cell should be skipped."""
        return is_current_month and day >= today_day

    def _extract_links_from_cell(
        self, cell: Locator, current_month: int, day: int
    ) -> Tuple[int, List[Tuple[str, str]]]:
        """Extract IPO links from calendar cell."""
        spacks_filtered = 0
        results = []
        
        links = cell.locator("table tr:nth-child(2) td a")
        
        for i in range(links.count()):
            link = links.nth(i)
            name_raw = link.inner_text().strip().replace("\n", " ")
            
            if "(상장)" not in name_raw:
                continue
            
            # utils 함수 사용
            if utils.is_spac_stock(name_raw):
                print(f"         [필터] {current_month}월 {day}일, '{name_raw}' 항목은 '스팩'이므로 건너뜁니다.")
                spacks_filtered += 1
                continue
            
            # utils 함수 사용
            name_cleaned = utils.clean_stock_name(name_raw)
            
            if href := link.get_attribute("href"):
                href_full = f"{self.BASE_URL}{href}"
                print(f"      [수집] {current_month}월 {day}일 | {name_cleaned} (원래: {name_raw})")
                results.append((name_cleaned, href_full))
        
        return spacks_filtered, results

    def _parse_calendar_cell(
        self, cell: Locator, current_month: int, today_day: int, is_current_month: bool
    ) -> Tuple[int, List[Tuple[str, str]]]:
        """Parse single calendar cell for IPO information."""
        day = self._extract_day_from_cell(cell)
        if day is None:
            return 0, []
        
        if self._should_skip_cell(day, current_month, today_day, is_current_month):
            return 0, []
        
        try:
            return self._extract_links_from_cell(cell, current_month, day)
        except Exception as e:
            print(f"         [오류] {current_month}월 {day}일 링크 파싱 실패: {e}")
            return 0, []

    def _parse_calendar_table(
        self, page: Page, month: int, today_day: int, is_current_month: bool
    ) -> Tuple[int, List[Tuple[str, str]]]:
        """Parse calendar table for a single month."""
        calendar_table = page.locator('table[summary="증시캘린더"]')
        
        if not calendar_table.is_visible():
            print(f"         [경고] {month}월 '증시캘린더' 테이블을 찾을 수 없습니다.")
            return 0, []
        
        cells = calendar_table.locator("tbody > tr > td")
        spacks_total = 0
        results_total = []
        
        for i in range(cells.count()):
            spack_count, cell_results = self._parse_calendar_cell(
                cells.nth(i), month, today_day, is_current_month
            )
            spacks_total += spack_count
            results_total.extend(cell_results)
        
        return spacks_total, results_total