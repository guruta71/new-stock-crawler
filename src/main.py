# src/main.py
import sys
import os
import datetime
import pandas as pd
from typing import List, Dict 

# 경로 설정
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.append(os.path.dirname(project_root)) 

from domain.ports import IPOInfoPort, PersistencePort
from infra.adapters.playwright_adapter import PlaywrightIPOAdapter
from domain.models import ScrapeReport, StockInfo
from infra.adapters.dataframe_adapter import convert_to_dataframe
from infra.adapters.excel_persistence_adapter import LocalExcelPersistenceAdapter

def run_scrape():
    print("--- 🚀 Playwright (상장) 종목 연도별 크롤링 시작 ---")

    today: datetime.date = datetime.date.today() 
    current_year: int = today.year      
    current_month: int = today.month    
    current_day: int = today.day        
    
    start_year: int = 2020 # ◀ 크롤링 시작 연도

    print(f"기준 날짜: {today}")
    print(f"크롤링 대상: {start_year}년 1월 1일 ~ {current_year}년 {current_month}월 {current_day-1}일(어제)까지")
    print("필터: (상장) 포함, '스팩' 제외")

    # --- 어댑터 의존성 주입 ---
    ipo_adapter: IPOInfoPort = PlaywrightIPOAdapter(headless=True)
    persistence_adapter: PersistencePort = LocalExcelPersistenceAdapter()
    
    # ▼▼▼ [수정] 연도별 DataFrame을 담을 딕셔너리 초기화 ▼▼▼
    yearly_dataframes: Dict[int, pd.DataFrame] = {}
    
    try:
        # --- 1. 셋업 (루프 밖에서 1회만 실행) ---
        ipo_adapter.setup()
        
        for year_to_scrape in range(start_year, current_year + 1):
            
            print(f"\n\n--- 🔄 [{year_to_scrape}년] 작업 시작 ---")
            
            # --- 연도별 탐색 범위 설정 ---
            if year_to_scrape == current_year:
                target_start_month = 1
                target_end_month = current_month
                target_day_limit = current_day 
            else:
                target_start_month = 1
                target_end_month = 12
                target_day_limit = 32 

            print(f"   (대상: {year_to_scrape}년 {target_start_month}월 ~ {target_end_month}월)")

            # --- 2. 1차 크롤링 (캘린더 목록) ---
            report: ScrapeReport = ipo_adapter.get_ipos_for_period(
                year=year_to_scrape,
                start_month=target_start_month,
                end_month=target_end_month,
                today_day=target_day_limit
            )
            
            print("   [성공] 1차 크롤링을 완료했습니다. ✅")
            
            print("\n   --- 📊 1차 요약 리포트 ---")
            print(f"    총 {report.spack_filtered_count}개의 '스팩' 종목을 제외했습니다.")
            print(f"    총 {report.final_stock_count}개의 (상장) 종목을 수집했습니다.")
            
            # --- 3. 2차 크롤링 & 3차 변환 ---
            if report.results:
                stock_details_list: List[StockInfo] = ipo_adapter.scrape_stock_details(report.results)
                
                print("\n   --- 🔄 DataFrame 변환 시작 ---")
                df: pd.DataFrame = convert_to_dataframe(stock_details_list)
                print("    [성공] DataFrame 변환 완료.")
                
                # ▼▼▼ [수정] 딕셔너리에 DataFrame 저장 (저장 X) ▼▼▼
                if not df.empty:
                    print(f"    [{year_to_scrape}년] 데이터 {len(df)}건 수집 완료.")
                    yearly_dataframes[year_to_scrape] = df
                else:
                    print(f"    [{year_to_scrape}년] 상세 정보 수집 실패 (결과 없음)")
                
            else:
                print("\n    (1차 수집된 종목 없음)")

        # --- 4. 엑셀 저장 (루프가 끝난 후 마지막에 1회 실행) ---
        if yearly_dataframes: # 딕셔너리에 데이터가 하나라도 있다면
            print("\n\n--- 💾 엑셀 파일 저장 시작 (모든 연도 통합) ---")
            persistence_adapter.save_report(yearly_dataframes)
        else:
            print("\n\n (저장할 데이터가 없어 엑셀 저장을 건너뜁니다)")

    except Exception as e:
        print(f"\n[실패] 크롤링 중 치명적 오류 발생: {e} ❌")
        
    finally:
        # --- 5. 정리 (루프 밖에서 1회만 실행) ---
        ipo_adapter.cleanup()
        print("\n\n--- 🏁 모든 크롤링 작업 종료 ---")

if __name__ == "__main__":
    run_scrape()