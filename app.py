from pathlib import Path
from typing import List, Optional, Tuple
import json
import math

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (
    QMainWindow,
    QTableWidgetItem,
)

import pandas as pd
import geopandas as gpd

from core.models import Bin, ExactValue
from core.data_handler import DataHandler
from ui.main_window import UIMainWindow
from utils.file_operations import save_png, save_svg, save_scheme, load_scheme

import os

BASE_DIR = os.path.dirname(__file__)
DEFAULT_GEOJSON_PATH = os.path.join(BASE_DIR, "data", "russia.geojson")

class ChoroplethApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Хороплет по регионам — конструктор (PyQt6)")
        self.resize(1200, 800)

        self.data_handler = DataHandler()
        self.ui = UIMainWindow(self)
        self.ui.connect_signals(self)
        self.on_open_default_geo(DEFAULT_GEOJSON_PATH)

        self.bins: List[Bin] = []
        self.exact_values: List[ExactValue] = []
        self.current_mode = "bins" # "bins" or "exact"
        self.no_data_color = "#D3D3D3"
        self.edge_color = "#444444"
        self.edge_width = 0.4

        self._update_style_ui()

    def _update_style_ui(self):
        self.ui.set_no_data_color_button_text(self.no_data_color)
        self.ui.set_edge_color_button_text(self.edge_color)
        self.ui.set_edge_width_spinbox_value(self.edge_width)

    # ---------------------- Обработчики ----------------------
    def on_open_geo(self):
        path = self.ui.get_file_dialog_open_file_name("Открыть геоданные", "GeoData (*.geojson *.json *.shp)")
        if not path:
            return
        try:
            self.data_handler.load_geojson(path)
            self.ui.get_geo_path_label().setText(Path(path).name)
            self.ui.clear_geo_key_combobox()
            cols = self.data_handler.get_gdf_columns()
            self.ui.add_items_to_geo_key_combobox(cols)
            if cols:
                self.ui.set_geo_key_combobox_current_index(0)
                self.data_handler.set_key_geo(cols[0])
            self._populate_value_table_from_gdf()
        except ValueError as e:
            self.ui.show_error_message("Ошибка чтения", str(e))

    def on_open_default_geo(self, path):
        if not path:
            return
        try:
            self.data_handler.load_geojson(path)
            self.ui.get_geo_path_label().setText(Path(path).name)
            self.ui.clear_geo_key_combobox()
            cols = self.data_handler.get_gdf_columns()
            self.ui.add_items_to_geo_key_combobox(cols)
            if cols:
                self.ui.set_geo_key_combobox_current_index(0)
                self.data_handler.set_key_geo(cols[0])
            self._populate_value_table_from_gdf()
        except ValueError as e:
            self.ui.show_error_message("Ошибка чтения", str(e))

    def on_geo_key_changed(self, text: str):
        self.data_handler.set_key_geo(text or None)
        self._populate_value_table_from_gdf()

    def on_open_csv(self):
        path = self.ui.get_file_dialog_open_file_name("Открыть CSV с показателями", "CSV (*.csv)")
        if not path:
            return
        try:
            self.data_handler.load_csv(path)
            self.ui.get_csv_path_label().setText(Path(path).name)
            self.ui.clear_csv_comboboxes()
            cols = self.data_handler.get_df_values_columns()
            self.ui.add_items_to_csv_comboboxes(cols)

            key_csv, val_csv = self.data_handler.get_csv_keys()
            if key_csv:
                self.ui.cmb_csv_key.setCurrentText(key_csv)
            if val_csv:
                self.ui.set_csv_val_combobox_current_index(cols.index(val_csv))

        except ValueError as e:
            self.ui.show_error_message("Ошибка чтения", str(e))

    def on_join(self):
        try:
            key_geo = self.ui.get_geo_key_combobox_current_text()
            key_csv = self.ui.get_csv_key_combobox_current_text()
            val_csv = self.ui.get_csv_val_combobox_current_text()

            if not key_geo or not key_csv or not val_csv:
                self.ui.show_warning_message("Поля не выбраны", "Укажите поля ключа и значения.")
                return

            self.data_handler.join_data(key_geo, key_csv, val_csv)
            self._populate_value_table_from_gdf()
            self.ui.show_info_message("Готово", "Данные объединены. Таблица значений обновлена.")
        except ValueError as e:
            self.ui.show_error_message("Ошибка", str(e))

    def _populate_value_table_from_gdf(self):
        self.ui.block_table_values_signals(True)
        self.ui.clear_table_values()

        data = self.data_handler.get_current_data_for_table()
        for i, (region, value) in enumerate(data):
            self.ui.insert_table_values_row(self.ui.get_table_values_row_count())
            item_region = QTableWidgetItem(str(region))
            item_region.setFlags(item_region.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.ui.set_table_values_item(i, 0, item_region)

            item_val = QTableWidgetItem("" if value is None else str(value))
            item_val.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.ui.set_table_values_item(i, 1, item_val)
        self.ui.block_table_values_signals(False)

    def on_table_value_edited(self, item: QTableWidgetItem):
        if item.column() != 1:
            return
        row_idx = item.row()
        text = (item.text() or "").strip()
        try:
            val = float(text) if text != "" else math.nan
        except ValueError:
            self.ui.show_warning_message("Некорректное значение", f"Нельзя преобразовать \'{text}\' в число.")
            return

        region_key_value = self.ui.get_table_values_item(row_idx, 0).text()
        self.data_handler.update_gdf_value(region_key_value, val)

    def on_add_bin(self):
        r = self.ui.get_bin_table_row_count()
        self.ui.insert_bin_table_row(r)
        self.ui.set_bin_table_item(r, 0, QTableWidgetItem("0"))
        self.ui.set_bin_table_item(r, 1, QTableWidgetItem("1"))
        self.ui.set_bin_table_item(r, 2, QTableWidgetItem("#ffffff"))

    def on_delete_bin(self):
        r = self.ui.get_selected_bin_row()
        if r >= 0:
            self.ui.remove_bin_table_row(r)

    def on_pick_color_for_selected_bin(self):
        r = self.ui.get_selected_bin_row()
        if r < 0:
            return
        cur = self.ui.get_bin_table_item(r, 2)
        start_hex = cur.text() if cur else "#ffffff"
        new_hex = self.ui.pick_color_button(cur, start_hex)
        if cur:
            cur.setText(new_hex)
        else:
            self.ui.set_bin_table_item(r, 2, QTableWidgetItem(new_hex))

    def on_mode_changed(self):
        if self.ui.get_radio_bins().isChecked():
            self.current_mode = "bins"
            self.ui.get_stacked_widget().setCurrentIndex(0) # Show bins table
        else:
            self.current_mode = "exact"
            self.ui.get_stacked_widget().setCurrentIndex(1) # Show exact values table
        self.on_plot()

    def on_add_exact_value(self):
        r = self.ui.get_exact_table_row_count()
        self.ui.insert_exact_table_row(r)
        self.ui.set_exact_table_item(r, 0, QTableWidgetItem("0"))
        self.ui.set_exact_table_item(r, 1, QTableWidgetItem("#ffffff"))

    def on_delete_exact_value(self):
        r = self.ui.get_selected_exact_row()
        if r >= 0:
            self.ui.remove_exact_table_row(r)

    def on_pick_color_for_selected_exact_value(self):
        r = self.ui.get_selected_exact_row()
        if r < 0:
            return
        cur = self.ui.get_exact_table_item(r, 1)
        start_hex = cur.text() if cur else "#ffffff"
        new_hex = self.ui.pick_color_button(cur, start_hex)
        if cur:
            cur.setText(new_hex)
        else:
            self.ui.set_exact_table_item(r, 1, QTableWidgetItem(new_hex))

    def on_exact_value_edited(self, item: QTableWidgetItem):
        if item.column() != 0:
            return
        row_idx = item.row()
        text = (item.text() or "").strip()
        try:
            val = float(text)
        except ValueError:
            self.ui.show_warning_message("Некорректное значение", f"Нельзя преобразовать \'{text}\' в число.")
            return



    def on_pick_no_data_color(self):
        current_color = self.ui.btn_no_data_color.text()
        new_color = self.ui.pick_color_button(self.ui.btn_no_data_color, current_color)
        self.no_data_color = new_color

    def on_pick_edge_color(self):
        current_color = self.ui.btn_edge_color.text()
        new_color = self.ui.pick_color_button(self.ui.btn_edge_color, current_color)
        self.edge_color = new_color

    def on_edge_width_changed(self, value: float):
        self.edge_width = value

    def on_plot(self):
        gdf = self.data_handler.get_gdf()
        if gdf is None:
            self.ui.show_warning_message("Нет данных", "Сначала загрузите и объедините геоданные с показателями.")
            return

        # Считываем интервалы из таблицы
        self.bins = []
        for r in range(self.ui.get_bin_table_row_count()):
            try:
                lower = float(self.ui.get_bin_table_item(r, 0).text())
                upper = float(self.ui.get_bin_table_item(r, 1).text())
                color_hex = self.ui.get_bin_table_item(r, 2).text()
                self.bins.append(Bin(lower, upper, color_hex))
            except (ValueError, AttributeError):
                self.ui.show_warning_message("Ошибка интервалов", f"Некорректные значения в строке интервалов {r+1}. Проверьте числа и цвета.")
                return

        if not self.bins and self.current_mode == "bins":
            self.ui.show_warning_message("Нет интервалов", "Добавьте хотя бы один интервал.")
            return

        # Считываем точные значения из таблицы
        self.exact_values = []
        if self.current_mode == "exact":
            for r in range(self.ui.get_exact_table_row_count()):
                try:
                    value = float(self.ui.get_exact_table_item(r, 0).text())
                    color_hex = self.ui.get_exact_table_item(r, 1).text()
                    self.exact_values.append(ExactValue(value, color_hex))
                except (ValueError, AttributeError):
                    self.ui.show_warning_message("Ошибка точных значений", f"Некорректные значения в строке точных значений {r+1}. Проверьте числа и цвета.")
                    return
            if not self.exact_values:
                self.ui.show_warning_message("Нет точных значений", "Добавьте хотя бы одно точное значение.")
                return

        # Очищаем предыдущий график
        self.ui.get_figure().clear()
        ax = self.ui.get_figure().add_subplot(111)

        # Применяем цвета к GeoDataFrame
        value_col = self.data_handler.get_value_column_name()
        gdf["__color__"] = gdf[value_col].apply(lambda x:
            self._get_color_for_value(x, self.bins, self.exact_values, self.no_data_color, self.current_mode)
        )

        # Рисуем карту
        gdf.plot(
            ax=ax,
            color=gdf["__color__"],
            edgecolor=self.edge_color,
            linewidth=self.edge_width,
            missing_kwds={
                "color": self.no_data_color,
                "edgecolor": self.edge_color,
                "linewidth": self.edge_width,
                "label": "Нет данных",
            },
        )

        ax.set_axis_off()
        # ax.set_title("Хороплет", fontsize=15)

        # Легенда
        # handles = []
        # labels = []
        # if self.current_mode == "bins":
        #     for i, b in enumerate(self.bins):
        #         label = f"{b.lower} – {b.upper}"
        #         handles.append(plt.Rectangle((0, 0), 1, 1, fc=b.color_hex))
        #         labels.append(label)
        # else: # exact mode
        #     for i, ev in enumerate(self.exact_values):
        #         label = f"{ev.value}"
        #         handles.append(plt.Rectangle((0, 0), 1, 1, fc=ev.color_hex))
        #         labels.append(label)

        # # Добавляем легенду для отсутствующих данных
        # handles.append(plt.Rectangle((0, 0), 1, 1, fc=self.no_data_color))
        # labels.append("Нет данных")
        #
        # ax.legend(handles, labels, loc="lower left", bbox_to_anchor=(1, 0))

        self.ui.get_figure().tight_layout()
        self.ui.get_figure_canvas().draw()

    def _get_color_for_value(self, value: float, bins: List[Bin], exact_values: List[ExactValue], no_data_color: str, mode: str) -> str:
        if pd.isna(value):
            return no_data_color

        if mode == "bins":
            for i, b in enumerate(bins):
                is_last = (i == len(bins) - 1)
                if b.contains(value, is_last):
                    return b.color_hex
        else: # exact mode
            for ev in exact_values:
                if value == ev.value:
                    return ev.color_hex

        return no_data_color # Если значение не попало ни в один интервал или точное значение

    def on_save_png(self):
        path = self.ui.get_file_dialog_save_file_name("Сохранить карту как PNG", "PNG (*.png)")
        if path:
            save_png(self.ui.get_figure(), path)
            self.ui.show_info_message("Сохранено", f"Карта сохранена в {path}")

    def on_save_svg(self):
        path = self.ui.get_file_dialog_save_file_name("Сохранить карту как SVG", "SVG (*.svg)")
        if path:
            save_svg(self.ui.get_figure(), path)
            self.ui.show_info_message("Сохранено", f"Карта сохранена в {path}")

    def on_save_scheme(self):
        path = self.ui.get_file_dialog_save_file_name("Сохранить схему", "JSON (*.json)")
        if not path:
            return

        scheme_data = {
            "mode": self.current_mode,
            "bins": [{
                "lower": b.lower,
                "upper": b.upper,
                "color_hex": b.color_hex
            } for b in self.bins],
            "exact_values": [{
                "value": ev.value,
                "color_hex": ev.color_hex
            } for ev in self.exact_values],
            "no_data_color": self.no_data_color,
            "edge_color": self.edge_color,
            "edge_width": self.edge_width,
        }
        save_scheme(scheme_data, path)
        self.ui.show_info_message("Сохранено", f"Схема сохранена в {path}")

    def on_load_scheme(self):
        path = self.ui.get_file_dialog_open_file_name("Загрузить схему", "JSON (*.json)")
        if not path:
            return

        try:
            scheme_data = load_scheme(path)
            self.current_mode = scheme_data.get("mode", "bins")

            self.bins = [
                Bin(b["lower"], b["upper"], b["color_hex"])
                for b in scheme_data.get("bins", [])
            ]
            self.exact_values = [
                ExactValue(ev["value"], ev["color_hex"])
                for ev in scheme_data.get("exact_values", [])
            ]
            self.no_data_color = scheme_data.get("no_data_color", "#D3D3D3")
            self.edge_color = scheme_data.get("edge_color", "#444444")
            self.edge_width = scheme_data.get("edge_width", 0.4)

            # Обновляем UI
            self._update_style_ui()

            self.ui.tbl_bins.setRowCount(0)
            for i, b in enumerate(self.bins):
                self.ui.insert_bin_table_row(i)
                self.ui.set_bin_table_item(i, 0, QTableWidgetItem(str(b.lower)))
                self.ui.set_bin_table_item(i, 1, QTableWidgetItem(str(b.upper)))
                self.ui.set_bin_table_item(i, 2, QTableWidgetItem(b.color_hex))

            self.ui.tbl_exact_values.setRowCount(0)
            for i, ev in enumerate(self.exact_values):
                self.ui.insert_exact_table_row(i)
                self.ui.set_exact_table_item(i, 0, QTableWidgetItem(str(ev.value)))
                self.ui.set_exact_table_item(i, 1, QTableWidgetItem(ev.color_hex))

            if self.current_mode == "bins":
                self.ui.get_radio_bins().setChecked(True)
                self.ui.get_stacked_widget().setCurrentIndex(0)
            else:
                self.ui.get_radio_exact().setChecked(True)
                self.ui.get_stacked_widget().setCurrentIndex(1)

            self.ui.show_info_message("Загружено", f"Схема загружена из {path}")
            self.on_plot() # Перерисовать карту с новой схемой

        except Exception as e:
            self.ui.show_error_message("Ошибка загрузки", f"Не удалось загрузить схему:\n{e}")

# import matplotlib.pyplot as plt


