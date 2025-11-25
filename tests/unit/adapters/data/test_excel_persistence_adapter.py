"""
LocalExcelPersistenceAdapter 단위 테스트
Excel 파일 저장 로직 검증
"""
import pytest
import pandas as pd
import os
import tempfile
import shutil
from pathlib import Path

from infra.adapters.excel_persistence_adapter import LocalExcelPersistenceAdapter


class TestLocalExcelPersistenceAdapter:
    """LocalExcelPersistenceAdapter 단위 테스트"""
    
    @pytest.fixture
    def temp_dir(self):
        """임시 디렉토리 생성"""
        import time
        import gc
        temp_path = tempfile.mkdtemp()
        yield temp_path
        # 테스트 후 정리 - Windows 파일 잠금 해제 대기
        gc.collect()  # garbage collection 강제 실행
        time.sleep(0.1)  # 파일 handle 해제 대기
        if os.path.exists(temp_path):
            try:
                shutil.rmtree(temp_path)
            except PermissionError:
                # Windows에서 파일이 아직 잠겨있을 수 있음
                time.sleep(0.5)
                shutil.rmtree(temp_path)
    
    @pytest.fixture
    def adapter(self, temp_dir, monkeypatch):
        """테스트용 어댑터 (임시 디렉토리 사용)"""
        # OUTPUT_DIR을 임시 디렉토리로 변경
        monkeypatch.setattr(
            'infra.adapters.excel_persistence_adapter.LocalExcelPersistenceAdapter.OUTPUT_DIR',
            temp_dir
        )
        return LocalExcelPersistenceAdapter()
    
    def test_initialization_creates_directory(self, temp_dir, monkeypatch):
        """초기화 시 디렉토리 생성 확인"""
        # Given
        test_dir = os.path.join(temp_dir, "test_reports")
        assert not os.path.exists(test_dir)
        
        monkeypatch.setattr(
            'infra.adapters.excel_persistence_adapter.LocalExcelPersistenceAdapter.OUTPUT_DIR',
            test_dir
        )
        
        # When
        adapter = LocalExcelPersistenceAdapter()
        
        # Then
        assert os.path.exists(test_dir)
    
    def test_save_single_year(self, adapter, temp_dir):
        """단일 연도 데이터 저장"""
        # Given
        df = pd.DataFrame({
            'name': ['Stock A', 'Stock B'],
            'price': [100, 200]
        })
        data = {2024: df}
        
        # When
        adapter.save_report(data)
        
        # Then
        filepath = os.path.join(temp_dir, adapter.FILENAME)
        assert os.path.exists(filepath)
        
        # 파일 내용 검증
        loaded = pd.read_excel(filepath, sheet_name='2024')
        pd.testing.assert_frame_equal(loaded, df)
    
    def test_save_multiple_years(self, adapter, temp_dir):
        """다중 연도 시트 저장"""
        # Given
        df_2023 = pd.DataFrame({'name': ['Stock 2023'], 'value': [100]})
        df_2024 = pd.DataFrame({'name': ['Stock 2024'], 'value': [200]})
        df_2025 = pd.DataFrame({'name': ['Stock 2025'], 'value': [300]})
        
        data = {
            2023: df_2023,
            2024: df_2024,
            2025: df_2025
        }
        
        # When
        adapter.save_report(data)
        
        # Then
        filepath = os.path.join(temp_dir, adapter.FILENAME)
        assert os.path.exists(filepath)
        
        # 모든 시트 검증
        loaded_2023 = pd.read_excel(filepath, sheet_name='2023')
        loaded_2024 = pd.read_excel(filepath, sheet_name='2024')
        loaded_2025 = pd.read_excel(filepath, sheet_name='2025')
        
        pd.testing.assert_frame_equal(loaded_2023, df_2023)
        pd.testing.assert_frame_equal(loaded_2024, df_2024)
        pd.testing.assert_frame_equal(loaded_2025, df_2025)
    
    def test_skip_empty_dataframe(self, adapter, temp_dir):
        """빈 DataFrame은 건너뛰기"""
        # Given
        df_valid = pd.DataFrame({'name': ['Stock A'], 'value': [100]})
        df_empty = pd.DataFrame()
        
        data = {
            2024: df_valid,
            2025: df_empty  # 빈 DataFrame
        }
        
        # When
        adapter.save_report(data)
        
        # Then
        filepath = os.path.join(temp_dir, adapter.FILENAME)
        excel_file = pd.ExcelFile(filepath)
        
        # 2024 시트는 있고, 2025 시트는 없어야 함
        assert '2024' in excel_file.sheet_names
        assert '2025' not in excel_file.sheet_names
    
    def test_overwrite_existing_file(self, adapter, temp_dir):
        """기존 파일 덮어쓰기"""
        # Given
        df_old = pd.DataFrame({'old': [1, 2, 3]})
        adapter.save_report({2023: df_old})
        
        df_new = pd.DataFrame({'new': [4, 5, 6]})
        
        # When
        adapter.save_report({2024: df_new})
        
        # Then
        filepath = os.path.join(temp_dir, adapter.FILENAME)
        excel_file = pd.ExcelFile(filepath)
        
        # 새 파일에는 2024 시트만 있어야 함
        assert '2024' in excel_file.sheet_names
        assert '2023' not in excel_file.sheet_names
    
    def test_filepath_construction(self, adapter, temp_dir):
        """파일 경로 생성 확인"""
        # When
        df = pd.DataFrame({'test': [1]})
        adapter.save_report({2024: df})
        
        # Then
        expected_path = os.path.join(temp_dir, "ipo_data_all_years.xlsx")
        assert os.path.exists(expected_path)
    
    def test_dataframe_with_various_dtypes(self, adapter, temp_dir):
        """다양한 데이터 타입 저장"""
        # Given
        df = pd.DataFrame({
            'string_col': ['A', 'B', 'C'],
            'int_col': [1, 2, 3],
            'float_col': [1.1, 2.2, 3.3],
            'bool_col': [True, False, True]
        })
        
        # When
        adapter.save_report({2024: df})
        
        # Then
        filepath = os.path.join(temp_dir, adapter.FILENAME)
        loaded = pd.read_excel(filepath, sheet_name='2024')
        
        assert len(loaded) == 3
        assert 'string_col' in loaded.columns
        assert 'int_col' in loaded.columns
        assert 'float_col' in loaded.columns
        assert 'bool_col' in loaded.columns
