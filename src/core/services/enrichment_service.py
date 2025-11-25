from typing import Dict
import pandas as pd
from core.ports.enrichment_ports import TickerMapperPort, MarketDataProviderPort
from core.ports.utility_ports import LoggerPort
from core.ports.data_ports import DataExporterPort

class EnrichmentService:
    """
    수집된 데이터에 추가 정보(시세, 성장률)를 보강하는 서비스
    """
    def __init__(
        self,
        ticker_mapper: TickerMapperPort,
        market_data_provider: MarketDataProviderPort,
        data_exporter: DataExporterPort,
        logger: LoggerPort
    ):
        self.ticker_mapper = ticker_mapper
        self.market_data_provider = market_data_provider
        self.data_exporter = data_exporter
        self.logger = logger

    def enrich_data(self, yearly_data: Dict[int, pd.DataFrame]) -> None:
        """
        데이터 보강 및 재저장
        """
        self.logger.info("=" * 60)
        self.logger.info("📈 데이터 보강 작업 시작 (OHLC, 성장률)")
        
        enriched_data = {}
        total_enriched = 0
        
        for year, df in yearly_data.items():
            if df.empty:
                continue
                
            self.logger.info(f"[{year}년] 데이터 보강 중... ({len(df)}건)")
            
            # 새로운 컬럼 초기화 (Ticker는 저장하지 않음)
            new_cols = ['Open', 'High', 'Low', 'Close', 'Growth_Rate']
            for col in new_cols:
                if col not in df.columns:
                    df[col] = None
            
            for index, row in df.iterrows():
                try:
                    # 1. Ticker 조회 (저장하지 않고 로직 내에서만 사용)
                    ticker = self.ticker_mapper.get_ticker(row['name'])
                    if not ticker:
                        continue
                    
                    # 2. OHLC 조회 (상장일 기준)
                    if pd.isna(row['listing_date']) or row['listing_date'] == "N/A":
                        continue
                        
                    # 날짜 형식 변환 (YYYY.MM.DD -> datetime)
                    listing_date_str = str(row['listing_date']).replace(".", "-")
                    listing_date = pd.to_datetime(listing_date_str).date()
                    
                    ohlc = self.market_data_provider.get_ohlc(ticker, listing_date)
                    
                    if ohlc:
                        df.at[index, 'Open'] = ohlc['Open']
                        df.at[index, 'High'] = ohlc['High']
                        df.at[index, 'Low'] = ohlc['Low']
                        df.at[index, 'Close'] = ohlc['Close']
                        
                        # 3. 성장률 계산 (종가 / 공모가 - 1) * 100
                        if pd.notna(row['confirmed_price']) and row['confirmed_price'] != "":
                            confirmed_price = float(row['confirmed_price'])
                            if confirmed_price > 0:
                                growth_rate = (ohlc['Close'] - confirmed_price) / confirmed_price * 100
                                df.at[index, 'Growth_Rate'] = round(growth_rate, 2)
                                total_enriched += 1
                                
                except Exception as e:
                    # 개별 실패는 로그를 남기지 않거나 디버그 레벨로
                    pass
            
            enriched_data[year] = df
            
        # 저장
        if enriched_data:
            self.data_exporter.export(enriched_data)
            self.logger.info(f"✅ 데이터 보강 완료 (총 {total_enriched}건 시세 추가됨)")
            self.logger.info("=" * 60)
