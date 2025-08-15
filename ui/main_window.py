from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QFileDialog,
    QRadioButton,
    QSpinBox,
    QDoubleSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

class UIMainWindow:
    def __init__(self, main_window: QMainWindow):
        self.main_window = main_window
        self.figure = Figure(figsize=(6, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self.main_window)

        # UI elements that need to be accessed by the main app logic
        self.lbl_geo_path = QLabel("— не загружено —")
        self.cmb_geo_key = QComboBox()
        self.lbl_csv_path = QLabel("— не загружено —")
        self.cmb_csv_key = QComboBox()
        self.cmb_csv_val = QComboBox()
        self.tbl_values = QTableWidget()
        self.tbl_bins = QTableWidget()
        self.btn_no_data_color = QPushButton("#D3D3D3")
        self.btn_edge_color = QPushButton("#444444")
        self.spin_edge_width = QDoubleSpinBox()

        # New UI elements for mode selection and exact values
        self.radio_bins = QRadioButton("Интервалы")
        self.radio_exact = QRadioButton("Точные значения")
        self.btn_group_mode = QButtonGroup()
        self.tbl_exact_values = QTableWidget()
        self.btn_add_exact = QPushButton("Добавить значение")
        self.btn_del_exact = QPushButton("Удалить выбранный")
        self.btn_color_exact = QPushButton("Выбрать цвет…")

        self._build_ui()

    def _build_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)

        tabs = QTabWidget()
        tabs.addTab(self._build_data_tab(), "Данные")
        tabs.addTab(self._build_bins_tab(), "Интервалы и цвета")
        tabs.addTab(self._build_style_tab(), "Стиль")

        left_layout.addWidget(tabs)
        left_layout.addWidget(self._build_actions_box())

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.addWidget(self.toolbar)
        right_layout.addWidget(self.canvas)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(1, 1)

        self.main_window.setCentralWidget(splitter)
        self._build_menu()

    def _build_menu(self):
        toolbar = QToolBar("Основные действия")
        self.main_window.addToolBar(toolbar)

        # Actions will be connected in ChoroplethApp
        self.act_open_geo = QAction("Открыть геоданные…", self.main_window)
        toolbar.addAction(self.act_open_geo)

        self.act_open_csv = QAction("Открыть CSV…", self.main_window)
        toolbar.addAction(self.act_open_csv)

        self.act_save_png = QAction("Сохранить PNG…", self.main_window)
        toolbar.addAction(self.act_save_png)

        self.act_save_svg = QAction("Сохранить SVG…", self.main_window)
        toolbar.addAction(self.act_save_svg)

        toolbar.addSeparator()

        self.act_load_scheme = QAction("Загрузить схему…", self.main_window)
        toolbar.addAction(self.act_load_scheme)

        self.act_save_scheme = QAction("Сохранить схему…", self.main_window)
        toolbar.addAction(self.act_save_scheme)

    def _build_data_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        g_group = QGroupBox("Геоданные (GeoJSON/Shapefile)")
        g_form = QFormLayout(g_group)
        self.btn_geo_open = QPushButton("Загрузить…")
        g_form.addRow("Файл:", self.lbl_geo_path)
        g_form.addRow("Поле региона:", self.cmb_geo_key)
        g_form.addRow(self.btn_geo_open)

        c_group = QGroupBox("Показатели (CSV)")
        c_form = QFormLayout(c_group)
        self.btn_csv_open = QPushButton("Загрузить…")
        self.btn_join = QPushButton("Объединить с геоданными")
        c_form.addRow("Файл:", self.lbl_csv_path)
        c_form.addRow("Столбец региона:", self.cmb_csv_key)
        c_form.addRow("Столбец значения:", self.cmb_csv_val)
        c_form.addRow(self.btn_csv_open)
        c_form.addRow(self.btn_join)

        self.tbl_values.setColumnCount(2)
        self.tbl_values.setHorizontalHeaderLabels(["Регион", "Значение"])
        self.tbl_values.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl_values.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        lay.addWidget(g_group)
        lay.addWidget(c_group)
        lay.addWidget(QLabel("Значения по регионам (двойной клик для редактирования):"))
        lay.addWidget(self.tbl_values)
        return w

    def _build_bins_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        # Mode selection
        mode_group_box = QGroupBox("Режим определения цвета")
        mode_layout = QHBoxLayout(mode_group_box)
        self.radio_bins.setChecked(True) # Default to bins mode
        mode_layout.addWidget(self.radio_bins)
        mode_layout.addWidget(self.radio_exact)
        self.btn_group_mode.addButton(self.radio_bins)
        self.btn_group_mode.addButton(self.radio_exact)
        lay.addWidget(mode_group_box)

        # Bins table setup
        self.tbl_bins.setColumnCount(3)
        self.tbl_bins.setHorizontalHeaderLabels(["От (вкл)", "До", "Цвет"])
        self.tbl_bins.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl_bins.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tbl_bins.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        bins_btns = QHBoxLayout()
        self.btn_add_bin = QPushButton("Добавить интервал")
        self.btn_del_bin = QPushButton("Удалить выбранный")
        self.btn_color_bin = QPushButton("Выбрать цвет…")
        bins_btns.addWidget(self.btn_add_bin)
        bins_btns.addWidget(self.btn_del_bin)
        bins_btns.addWidget(self.btn_color_bin)

        # Exact values table setup
        self.tbl_exact_values.setColumnCount(2)
        self.tbl_exact_values.setHorizontalHeaderLabels(["Значение", "Цвет"])
        self.tbl_exact_values.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.tbl_exact_values.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        exact_btns = QHBoxLayout()
        self.btn_add_exact = QPushButton("Добавить значение")
        self.btn_del_exact = QPushButton("Удалить выбранный")
        self.btn_color_exact = QPushButton("Выбрать цвет…")
        exact_btns.addWidget(self.btn_add_exact)
        exact_btns.addWidget(self.btn_del_exact)
        exact_btns.addWidget(self.btn_color_exact)

        # Stacked widget to switch between tables
        self.stacked_widget = QStackedWidget()
        bins_widget = QWidget()
        bins_layout = QVBoxLayout(bins_widget)
        bins_layout.addWidget(self.tbl_bins)
        bins_layout.addLayout(bins_btns)
        bins_layout.addWidget(QLabel("Правило принадлежности: все интервалы [от, до), кроме последнего — [от, до]."))
        self.stacked_widget.addWidget(bins_widget)

        exact_widget = QWidget()
        exact_layout = QVBoxLayout(exact_widget)
        exact_layout.addWidget(self.tbl_exact_values)
        exact_layout.addLayout(exact_btns)
        self.stacked_widget.addWidget(exact_widget)

        lay.addWidget(self.stacked_widget)
        return w

    def _build_style_tab(self) -> QWidget:
        w = QWidget()
        form = QFormLayout(w)

        self.spin_edge_width.setDecimals(2)
        self.spin_edge_width.setRange(0.0, 5.0)
        self.spin_edge_width.setValue(0.4)

        form.addRow("Цвет для отсутствующих значений:", self.btn_no_data_color)
        form.addRow("Цвет границ регионов:", self.btn_edge_color)
        form.addRow("Толщина границ:", self.spin_edge_width)
        return w

    def _build_actions_box(self) -> QWidget:
        box = QGroupBox("Действия")
        lay = QHBoxLayout(box)
        self.btn_plot = QPushButton("Построить карту")
        lay.addWidget(self.btn_plot)
        return box

    def pick_color_button(self, button: QPushButton, initial_color_hex: str) -> str:
        qc = QColorDialog.getColor(QColor(initial_color_hex), self.main_window, "Выбор цвета")
        if qc.isValid():
            new_hex = qc.name()
            button.setText(new_hex)
            return new_hex
        return initial_color_hex

    def show_error_message(self, title: str, message: str):
        QMessageBox.critical(self.main_window, title, message)

    def show_warning_message(self, title: str, message: str):
        QMessageBox.warning(self.main_window, title, message)

    def show_info_message(self, title: str, message: str):
        QMessageBox.information(self.main_window, title, message)

    def get_selected_bin_row(self) -> int:
        return self.tbl_bins.currentRow()

    def get_bin_table_item(self, row: int, col: int) -> QTableWidgetItem:
        return self.tbl_bins.item(row, col)

    def set_bin_table_item(self, row: int, col: int, item: QTableWidgetItem):
        self.tbl_bins.setItem(row, col, item)

    def get_bin_table_row_count(self) -> int:
        return self.tbl_bins.rowCount()

    def insert_bin_table_row(self, row: int):
        self.tbl_bins.insertRow(row)

    def remove_bin_table_row(self, row: int):
        self.tbl_bins.removeRow(row)

    def get_table_values_row_count(self) -> int:
        return self.tbl_values.rowCount()

    def insert_table_values_row(self, row: int):
        self.tbl_values.insertRow(row)

    def set_table_values_item(self, row: int, col: int, item: QTableWidgetItem):
        self.tbl_values.setItem(row, col, item)

    def get_table_values_item(self, row: int, col: int) -> QTableWidgetItem:
        return self.tbl_values.item(row, col)

    def block_table_values_signals(self, block: bool):
        self.tbl_values.blockSignals(block)

    def clear_table_values(self):
        self.tbl_values.setRowCount(0)

    def get_file_dialog_open_file_name(self, title: str, filter: str) -> str:
        path, _ = QFileDialog.getOpenFileName(self.main_window, title, "", filter)
        return path

    def get_file_dialog_save_file_name(self, title: str, filter: str) -> str:
        path, _ = QFileDialog.getSaveFileName(self.main_window, title, "", filter)
        return path

    def clear_geo_key_combobox(self):
        self.cmb_geo_key.clear()

    def add_items_to_geo_key_combobox(self, items: list[str]):
        self.cmb_geo_key.addItems(items)

    def set_geo_key_combobox_current_index(self, index: int):
        self.cmb_geo_key.setCurrentIndex(index)

    def get_geo_key_combobox_current_text(self) -> str:
        return self.cmb_geo_key.currentText()

    def clear_csv_comboboxes(self):
        self.cmb_csv_key.clear()
        self.cmb_csv_val.clear()

    def add_items_to_csv_comboboxes(self, items: list[str]):
        self.cmb_csv_key.addItems(items)
        self.cmb_csv_val.addItems(items)

    def set_csv_val_combobox_current_index(self, index: int):
        self.cmb_csv_val.setCurrentIndex(index)

    def get_csv_key_combobox_current_text(self) -> str:
        return self.cmb_csv_key.currentText()

    def get_csv_val_combobox_current_text(self) -> str:
        return self.cmb_csv_val.currentText()

    def get_edge_width_spinbox_value(self) -> float:
        return self.spin_edge_width.value()

    def set_edge_width_spinbox_value(self, value: float):
        self.spin_edge_width.setValue(value)

    def get_no_data_color_button_text(self) -> str:
        return self.btn_no_data_color.text()

    def set_no_data_color_button_text(self, text: str):
        self.btn_no_data_color.setText(text)

    def get_edge_color_button_text(self) -> str:
        return self.btn_edge_color.text()

    def set_edge_color_button_text(self, text: str):
        self.btn_edge_color.setText(text)

    def get_figure_canvas(self):
        return self.canvas

    def get_figure(self):
        return self.figure

    def get_geo_path_label(self) -> QLabel:
        return self.lbl_geo_path

    def get_csv_path_label(self) -> QLabel:
        return self.lbl_csv_path

    def connect_signals(self, app_instance):
        # Connect UI elements to methods in ChoroplethApp
        self.act_open_geo.triggered.connect(app_instance.on_open_geo)
        self.act_open_csv.triggered.connect(app_instance.on_open_csv)
        self.act_save_png.triggered.connect(app_instance.on_save_png)
        self.act_save_svg.triggered.connect(app_instance.on_save_svg)
        self.act_load_scheme.triggered.connect(app_instance.on_load_scheme)
        self.act_save_scheme.triggered.connect(app_instance.on_save_scheme)

        self.cmb_geo_key.currentTextChanged.connect(app_instance.on_geo_key_changed)
        self.btn_geo_open.clicked.connect(app_instance.on_open_geo)
        self.btn_csv_open.clicked.connect(app_instance.on_open_csv)
        self.btn_join.clicked.connect(app_instance.on_join)
        self.tbl_values.itemChanged.connect(app_instance.on_table_value_edited)

        self.btn_add_bin.clicked.connect(app_instance.on_add_bin)
        self.btn_del_bin.clicked.connect(app_instance.on_delete_bin)
        self.btn_color_bin.clicked.connect(app_instance.on_pick_color_for_selected_bin)

        self.btn_no_data_color.clicked.connect(lambda: app_instance.on_pick_no_data_color())
        self.btn_edge_color.clicked.connect(lambda: app_instance.on_pick_edge_color())
        self.spin_edge_width.valueChanged.connect(app_instance.on_edge_width_changed)

        self.btn_plot.clicked.connect(app_instance.on_plot)

        self.radio_bins.toggled.connect(app_instance.on_mode_changed)
        self.btn_add_exact.clicked.connect(app_instance.on_add_exact_value)
        self.btn_del_exact.clicked.connect(app_instance.on_delete_exact_value)
        self.btn_color_exact.clicked.connect(app_instance.on_pick_color_for_selected_exact_value)
        self.tbl_exact_values.itemChanged.connect(app_instance.on_exact_value_edited)





    def get_radio_bins(self) -> QRadioButton:
        return self.radio_bins

    def get_radio_exact(self) -> QRadioButton:
        return self.radio_exact

    def get_stacked_widget(self):
        return self.stacked_widget

    def get_exact_table_row_count(self) -> int:
        return self.tbl_exact_values.rowCount()

    def insert_exact_table_row(self, row: int):
        self.tbl_exact_values.insertRow(row)

    def set_exact_table_item(self, row: int, col: int, item: QTableWidgetItem):
        self.tbl_exact_values.setItem(row, col, item)

    def get_exact_table_item(self, row: int, col: int) -> QTableWidgetItem:
        return self.tbl_exact_values.item(row, col)

    def get_selected_exact_row(self) -> int:
        return self.tbl_exact_values.currentRow()

    def remove_exact_table_row(self, row: int):
        self.tbl_exact_values.removeRow(row)

    def block_exact_table_signals(self, block: bool):
        self.tbl_exact_values.blockSignals(block)

    def clear_exact_table(self):
        self.tbl_exact_values.setRowCount(0)


