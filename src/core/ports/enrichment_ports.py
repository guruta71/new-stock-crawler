from abc import ABC, abstractmethod
from typing import Optional, Dict
from datetime import date

class TickerMapperPort(ABC):
    """종목명으로 티커(종목코드)를 조회하는 포트"""
    @abstractmethod
    def get_ticker(self, stock_name: str) -> Optional[str]:
        pass

class MarketDataProviderPort(ABC):
    """시세 데이터를 조회하는 포트"""
    @abstractmethod
    def get_ohlc(self, ticker: str, target_date: date) -> Optional[Dict[str, int]]:
        """
        특정 날짜의 OHLC(시가, 고가, 저가, 종가) 데이터를 조회
        Returns:
            {"Open": 1000, "High": 1100, "Low": 900, "Close": 1050}
        """
        pass
