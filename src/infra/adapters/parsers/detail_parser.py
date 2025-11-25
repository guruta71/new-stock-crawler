import time
import traceback
from typing import List, Tuple, Optional, Dict
from playwright.sync_api import Page, Locator

from core.domain.models import StockInfo
from infra.adapters.parsers import utils  # 분리된 유틸리티 함수 임포트
from infra.adapters.parsers.table_grid_builder import TableGridBuilder # 테이블 변환기 임포트
from infra.adapters.parsers.strategies import (
    TableFinderStrategy,
    TitleSiblingTableFinder,
    TitleFollowingTableFinder,
    HeaderContentTableFinder,
    RowContentTableFinder
)

class StockDetailParser:

    def __init__(self, page: Page):
        self.page = page
        self.grid_builder = TableGridBuilder()
        
        # 전략 초기화
        self.table_strategies: List[TableFinderStrategy] = [
            TitleSiblingTableFinder(),
            TitleFollowingTableFinder(),
            HeaderContentTableFinder(),
            RowContentTableFinder()
        ]
        
        print("StockDetailParser (2차 파서) 초기화됨")

    def scrape_details(self, stocks: List[Tuple[str, str]]) -> List[StockInfo]:
        """Scrape detailed information for multiple stocks."""
        print("\n--- 'scrape_details' (DetailParser) 실행 ---")
        
        if not self.page or self.page.is_closed():
            print("   [오류] Page 객체가 초기화되지 않았거나 닫혔습니다.")
            return []
        
        if not stocks:
            print("   [정보] 전달된 종목 리스트가 없습니다.")
            return []

        collected_stocks = []
        
        for index, (name, href) in enumerate(stocks):
            print(f"\n   [{index + 1}/{len(stocks)}] '{name}' 세부 정보 파싱 시작...")
            print(f"      URL: {href}")
            
            if stock_info := self._scrape_single_stock(name, href):
                collected_stocks.append(stock_info)
            
            time.sleep(0.3)
        
        print("\n--- 'scrape_details' (전체) 완료 ---")
        return collected_stocks

    def _scrape_single_stock(self, name: str, href: str) -> Optional[StockInfo]:
        """Scrape detailed information for a single stock."""
        try:
            self.page.goto(href)
            self.page.wait_for_load_state("networkidle")
            
            company_info = self._parse_company_info()
            offering_info = self._parse_offering_info()
            schedule_info = self._parse_schedule_info()
            # 복잡한 로직은 _parse_shareholder_table에 캡슐화
            tradable_info = self._parse_shareholder_table()
            
            return self._create_stock_info(
                name, href, company_info, offering_info, schedule_info, tradable_info
            )
        except Exception as e:
            print(f"      [오류] '{name}' ({href}) 페이지 방문/파싱 실패: {e}")
            return None

    def _get_detail_value(self, table: Locator, key_text: str) -> str:
        """Extract value from key-value table."""
        try:
            key_cell = table.locator(
                f'//*[self::td or self::th][contains(normalize-space(.), "{key_text}")]'
            )
            value_cell = key_cell.locator("xpath=./following-sibling::td[1]")
            
            if value_cell.is_visible(timeout=1000):
                return value_cell.inner_text().replace("\u00a0", " ").strip()
            
            # 일부 구조가 다른 경우를 대비해 .first 사용
            key_cell = key_cell.first
            value_cell = key_cell.locator("xpath=./following-sibling::td[1]")
            
            if value_cell.is_visible(timeout=1000):
                return value_cell.inner_text().replace("\u00a0", " ").strip()
            
            print(f"      [경고] '{key_text}'의 값(value) 셀을 찾았으나 보이지 않습니다.")
            return "N/A"
        except Exception:
            print(f"      [경고] '{key_text}' 키를 테이블에서 찾지 못했습니다.")
            return "N/A"

    def _parse_company_info(self) -> dict:
        """Parse company overview table."""
        table = self.page.locator('table[summary="기업개요"]')
        return {
            "market": self._get_detail_value(table, "시장구분"),
            "sector": self._get_detail_value(table, "업종"),
            "revenue": self._get_detail_value(table, "매출액"),
            "profit_pre_tax": self._get_detail_value(table, "법인세비용차감전"),
            "net_profit": self._get_detail_value(table, "순이익"),
            "capital": self._get_detail_value(table, "자본금"),
        }

    def _parse_offering_info(self) -> dict:
        """Parse public offering information table."""
        table = self.page.locator('table[summary="공모정보"]')
        return {
            "total_shares": self._get_detail_value(table, "총공모주식수"),
            "par_value": self._get_detail_value(table, "액면가"),
            "desired_price": self._get_detail_value(table, "희망공모가액"),
            "confirmed_price": self._get_detail_value(table, "확정공모가"),
            "offering_amount": self._get_detail_value(table, "공모금액"),
            "underwriter": self._get_detail_value(table, "주간사"),
        }

    def _parse_schedule_info(self) -> dict:
        """Parse offering schedule information table."""
        table = self.page.locator('table[summary="공모청약일정"]')
        
        listing_date = self._get_detail_value(table, "신규상장일")
        if listing_date == "N/A":
            listing_date = self._get_detail_value(table, "(상장일") # 대체 키워드
        
        competition_rate_raw = self._get_detail_value(table, "기관경쟁률")
        
        return {
            "listing_date": listing_date,
            "competition_rate": utils.format_competition_rate(competition_rate_raw), # utils 사용
            "emp_shares": utils.extract_share_count( # utils 사용
                self._get_detail_value(table, "우리사주조합")
            ),
            "inst_shares": utils.extract_share_count( # utils 사용
                self._get_detail_value(table, "기관투자자등")
            ),
            "retail_shares": utils.extract_share_count( # utils 사용
                self._get_detail_value(table, "일반청약자")
            ),
        }

    def _create_stock_info(
        self, name: str, href: str, company_info: dict, offering_info: dict, schedule_info: dict, tradable_info: Tuple[str, str]
    ) -> StockInfo:
        """Create StockInfo object from parsed data."""
        return StockInfo(
            name=name,
            url=href,
            market_segment=company_info["market"],
            sector=company_info["sector"],
            revenue=utils.parse_to_int(company_info["revenue"]), # utils 사용
            profit_pre_tax=utils.parse_to_int(company_info["profit_pre_tax"]), # utils 사용
            net_profit=utils.parse_to_int(company_info["net_profit"]), # utils 사용
            capital=utils.parse_to_int(company_info["capital"]), # utils 사용
            total_shares=utils.parse_to_int(offering_info["total_shares"]), # utils 사용
            par_value=utils.parse_to_int(offering_info["par_value"]), # utils 사용
            desired_price_range=offering_info["desired_price"],
            confirmed_price=utils.parse_to_int(offering_info["confirmed_price"]), # utils 사용
            offering_amount=utils.parse_to_int(offering_info["offering_amount"]), # utils 사용
            underwriter=offering_info["underwriter"],
            listing_date=schedule_info["listing_date"],
            competition_rate=schedule_info["competition_rate"],
            emp_shares=utils.parse_to_int(schedule_info["emp_shares"]), # utils 사용
            inst_shares=utils.parse_to_int(schedule_info["inst_shares"]), # utils 사용
            retail_shares=utils.parse_to_int(schedule_info["retail_shares"]), # utils 사용
            tradable_shares_count=tradable_info[0],
            tradable_shares_percent=tradable_info[1],
        )

    # --- 주주 현황 (유통 가능 물량) 테이블 파싱 로직 ---

    def _parse_shareholder_table(self) -> Tuple[str, str]:
        """Parse shareholder table to extract tradable shares information."""
        try:
            table = self._find_shareholder_table()
            if table is None:
                print("      [정보] '주주현황' 테이블을 찾을 수 없습니다. (N/A 처리)")
                return "N/A", "N/A"
            
            # TableGridBuilder를 사용하여 복잡한 테이블을 그리드로 변환
            grid = self.grid_builder.build_grid(table)
            if not grid:
                print("      [경고] 테이블 그리드 변환 실패")
                return "N/A", "N/A"
            
            tradable_cols = self._find_tradable_columns(grid)
            if not tradable_cols:
                return "N/A", "N/A"
            
            count, percent = self._extract_tradable_values(grid, tradable_cols)
            print(f"      [결과] 유통가능물량: {count} ({percent})")
            
            return count, percent
        except Exception as e:
            print(f"      [오류] '주주현황' 테이블 파싱 중 예외 발생: {e}")
            traceback.print_exc()
            return "N/A", "N/A"

    def _find_shareholder_table(self) -> Optional[Locator]:
        """Find shareholder table using multiple strategies."""
        try:
            for strategy in self.table_strategies:
                if table := strategy.find_table(self.page):
                    return table
            
            print("      [경고] 모든 전략으로 테이블을 찾지 못했습니다.")
            return None
        except Exception as e:
            print(f"      [오류] 테이블 찾기 중 예외: {e}")
            return None

    def _find_tradable_column_in_header(self, grid: List[List[str]]) -> Optional[int]:
        """Find 'tradable shares' column index in header rows."""
        for row_idx in range(min(5, len(grid))):
            for col_idx, cell_text in enumerate(grid[row_idx]):
                if "유통가능" in cell_text and "물량" in cell_text:
                    print(f"      [정보] '유통가능물량' 헤더 발견: 행{row_idx}, 열{col_idx}")
                    return col_idx
        return None

    def _calculate_colspan_range(self, grid: List[List[str]], row_idx: int, col_idx: int) -> int:
        """Calculate colspan range for a merged cell."""
        colspan_end = col_idx
        cell_value = grid[row_idx][col_idx]
        
        while colspan_end < len(grid[row_idx]) - 1 and grid[row_idx][colspan_end + 1] == cell_value:
            colspan_end += 1
        
        return colspan_end

    def _find_sub_columns(
        self, grid: List[List[str]], header_row_idx: int, header_col_idx: int
    ) -> List[int]:
        """Find sub-column indices for shares count and percentage."""
        if header_row_idx + 1 >= len(grid):
            return [header_col_idx, header_col_idx + 1] # 다음 행이 없으면 기본값
        
        next_row = grid[header_row_idx + 1]
        colspan_end = self._calculate_colspan_range(grid, header_row_idx, header_col_idx)
        
        sub_cols = []
        for col in range(header_col_idx, min(colspan_end + 1, len(next_row))):
            sub_cell = next_row[col].strip()
            if sub_cell and sub_cell not in ("-", "", "　"):
                if "주식수" in sub_cell or "주식" in sub_cell:
                    sub_cols.append(col)
                elif "지분율" in sub_cell or "%" in sub_cell:
                    sub_cols.append(col)
        
        return sub_cols if sub_cols else [header_col_idx, header_col_idx + 1]

    def _find_tradable_columns(self, grid: List[List[str]]) -> List[int]:
        """Find column indices for tradable shares data."""
        header_col = self._find_tradable_column_in_header(grid)
        
        if header_col is None:
            print("      [경고] '유통가능물량' 열을 찾을 수 없습니다.")
            return []
        
        for row_idx in range(min(5, len(grid))):
            if "유통가능" in grid[row_idx][header_col] and "물량" in grid[row_idx][header_col]:
                sub_cols = self._find_sub_columns(grid, row_idx, header_col)
                print(f"      [정보] '유통가능물량' 열 인덱스: {sub_cols}")
                return sub_cols
        
        return [header_col, header_col + 1] # 하위 열 찾기 실패 시

    def _extract_tradable_values(
        self, grid: List[List[str]], tradable_cols: List[int]
    ) -> Tuple[str, str]:
        """Extract tradable shares count and percentage from last row."""
        last_row = grid[-1]
        
        count = (
            last_row[tradable_cols[0]].strip()
            if len(tradable_cols) > 0 and tradable_cols[0] < len(last_row)
            else "N/A"
        )
        
        percent = (
            last_row[tradable_cols[1]].strip()
            if len(tradable_cols) > 1 and tradable_cols[1] < len(last_row)
            else "N/A"
        )
        
        return utils.clean_tradable_values(count, percent) # utils 사용