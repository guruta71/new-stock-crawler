"""
데이터 처리 관련 포트 인터페이스
"""
from abc import ABC, abstractmethod
from typing import List, Dict
import pandas as pd
from core.domain.models import StockInfo


class DataMapperPort(ABC):
    """
    데이터 변환 포트
    
    책임: StockInfo를 DataFrame으로 변환
    """
    
    @abstractmethod
    def to_dataframe(self, stocks: List[StockInfo]) -> pd.DataFrame:
        """StockInfo 리스트를 DataFrame으로 변환"""
        pass


class DataExporterPort(ABC):
    """
    데이터 내보내기 포트
    
    책임: DataFrame을 외부 형식으로 저장
    """
    
    @abstractmethod
    def export(self, data: Dict[int, pd.DataFrame]) -> None:
        """연도별 데이터를 저장"""
        pass
