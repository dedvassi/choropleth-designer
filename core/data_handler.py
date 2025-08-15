from typing import Optional
import pandas as pd
import geopandas as gpd
import math

class DataHandler:
    def __init__(self):
        self.gdf: Optional[gpd.GeoDataFrame] = None
        self.key_geo: Optional[str] = None
        self.df_values: Optional[pd.DataFrame] = None
        self.key_csv: Optional[str] = None
        self.val_csv: Optional[str] = None
        self.value_col: str = "__value__"

    def load_geojson(self, path: str) -> bool:
        try:
            gdf = gpd.read_file(path)
        except Exception as e:
            raise ValueError(f"Не удалось прочитать файл геоданных:\n{e}")
        if gdf.empty or "geometry" not in gdf.columns:
            raise ValueError("В файле не найдены геометрии.")

        try:
            gdf = gdf.to_crs("EPSG:3995")
        except Exception as e:
            print(f"Предупреждение: Не удалось перепроецировать:\n{e}")

        self.gdf = gdf
        cols = [c for c in gdf.columns if c != "geometry"]
        if cols:
            self.key_geo = cols[0]
        return True

    def load_csv(self, path: str) -> bool:
        try:
            df = pd.read_csv(path)
        except Exception as e:
            raise ValueError(f"Не удалось прочитать CSV:\n{e}")
        if df.empty:
            raise ValueError("CSV пуст или не содержит данных.")

        self.df_values = df
        return True

    def join_data(self, key_geo: str, key_csv: str, val_csv: str):
        if self.gdf is None:
            raise ValueError("Геоданные не загружены.")
        if self.df_values is None:
            raise ValueError("CSV данные не загружены.")

        gdf_copy = self.gdf.copy()
        df_copy = self.df_values.copy()

        gdf_copy[key_geo] = gdf_copy[key_geo].astype(str).str.strip()
        df_copy[key_csv] = df_copy[key_csv].astype(str).str.strip()

        merged = gdf_copy.merge(df_copy[[key_csv, val_csv]], left_on=key_geo, right_on=key_csv, how="left")
        merged[self.value_col] = pd.to_numeric(merged[val_csv], errors="coerce")
        self.gdf = merged.drop(columns=[key_csv])

    def update_gdf_value(self, region_key_value: str, new_value: float):
        if self.gdf is None or self.key_geo is None:
            return
        self.gdf.loc[self.gdf[self.key_geo] == region_key_value, self.value_col] = new_value

    def get_gdf_columns(self) -> list[str]:
        if self.gdf is None:
            return []
        return [c for c in self.gdf.columns if c != "geometry"]

    def get_df_values_columns(self) -> list[str]:
        if self.df_values is None:
            return []
        return list(self.df_values.columns)

    def get_current_data_for_table(self) -> list[tuple[str, Optional[float]]]:
        if self.gdf is None or self.key_geo is None:
            return []
        data = []
        for _, row in self.gdf.iterrows():
            region = str(row[self.key_geo])
            value = row.get(self.value_col)
            data.append((region, value if not pd.isna(value) else None))
        return data

    def get_value_column_name(self) -> str:
        return self.value_col

    def get_gdf(self) -> Optional[gpd.GeoDataFrame]:
        return self.gdf

    def get_key_geo(self) -> Optional[str]:
        return self.key_geo

    def set_key_geo(self, key: str):
        self.key_geo = key

    def get_df_values(self) -> Optional[pd.DataFrame]:
        return self.df_values

    def get_csv_keys(self) -> tuple[Optional[str], Optional[str]]:
        if self.df_values is None:
            return None, None
        cols = list(self.df_values.columns)
        key_csv = cols[0] if cols else None
        val_csv = None
        for name in cols:
            if name.lower() in {"value", "val", "значение", "indicator", "показатель"}:
                val_csv = name
                break
        return key_csv, val_csv



