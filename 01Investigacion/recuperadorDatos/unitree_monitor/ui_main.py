"""
Interfaz gráfica principal — Monitor de motores Unitree.
"""

import csv
import subprocess
import platform
import time
from collections import deque
from datetime import datetime

import pyqtgraph as pg
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QGroupBox, QStatusBar,
    QGridLayout, QTabWidget, QDialog, QDialogButtonBox,
    QCheckBox, QScrollArea, QFrame, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from unitree_monitor.dds_reader import DDSReader
from unitree_monitor.joint_maps import get_joint_map, get_num_motors

pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")

# Colores para curvas de motores (hasta 29 para G1)
_MOTOR_COLORS = [
    "#e53935", "#8e24aa", "#1e88e5", "#00acc1", "#43a047", "#fb8c00",
    "#6d4c41", "#546e7a", "#e91e63", "#3949ab", "#00897b", "#c0ca33",
    "#f4511e", "#039be5", "#7cb342", "#fdd835", "#ff7043", "#ab47bc",
    "#26c6da", "#66bb6a", "#ffa726", "#8d6e63", "#78909c", "#ec407a",
    "#5c6bc0", "#26a69a", "#d4e157", "#ff5722", "#ba68c8",
]

# Tooltips educativos por tipo de articulación
_JOINT_TIPS = {
    "Hip":      "Cadera: controla el movimiento lateral de la pata (abducción/aducción)",
    "Thigh":    "Muslo: controla la flexión/extensión de la pata sobre la cadera",
    "Calf":     "Pantorrilla: controla la flexión de la rodilla",
    "Pitch":    "Movimiento de flexión/extensión (plano sagital)",
    "Roll":     "Movimiento lateral (plano frontal)",
    "Yaw":      "Rotación sobre el eje vertical (plano transversal)",
    "Knee":     "Rodilla: flexión/extensión de la pierna",
    "Ankle":    "Tobillo: estabilidad y contacto con el suelo",
    "Shoulder": "Hombro: articulación principal del brazo",
    "Elbow":    "Codo: flexión/extensión del antebrazo",
    "Wrist":    "Muñeca: orientación de la mano",
    "Waist":    "Cintura: rotación del torso",
}


def _joint_tooltip(motor_name: str) -> str:
    for key, tip in _JOINT_TIPS.items():
        if key in motor_name:
            return tip
    return ""


# ── GraphPanel ─────────────────────────────────────────────────────────────────

class GraphPanel(QWidget):
    """Gráficos en tiempo real con selector lateral de gráficos visibles."""

    HISTORY = 300  # muestras (30 s a 10 Hz)

    # Orden y etiquetas de los gráficos disponibles
    _GRAPH_KEYS = [
        "angle",
        "temp",
        "current",
        "voltage",
        "soc",
        "cells",
    ]
    _GRAPH_LABELS = {
        "angle":   "Ángulo por motor",
        "temp":    "Temperatura motores",
        "current": "Corriente sistema",
        "voltage": "Tensión sistema",
        "soc":     "Carga batería (SOC)",
        "cells":   "Tensión de celdas",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self._time_start    = None
        self._times         = deque(maxlen=self.HISTORY)
        self._motor_data    = {}   # idx -> {"q_deg": deque, "temperature": deque}
        self._motor_info    = {}   # idx -> {name, group}
        self._angle_curves  = {}   # idx -> PlotDataItem
        self._temp_curves   = {}   # idx -> PlotDataItem
        self._power_a_buf   = deque(maxlen=self.HISTORY)
        self._power_v_buf   = deque(maxlen=self.HISTORY)
        self._bms_soc_buf   = deque(maxlen=self.HISTORY)
        self._cell_vol_bufs = {}   # cell_idx -> deque
        self._curve_current = None
        self._curve_voltage = None
        self._curve_soc     = None
        self._cell_curves   = {}   # cell_idx -> PlotDataItem

        # checkboxes dict: key -> QCheckBox
        self._checkboxes: dict[str, QCheckBox] = {}

        self._build_ui()

    # ── Construcción de la UI ──────────────────────────────────────────────────

    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(4, 4, 4, 4)
        root.setSpacing(6)

        # ── Sidebar izquierdo ──────────────────────────────────────────────────
        sidebar = QWidget()
        sidebar.setFixedWidth(190)
        sidebar.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(4, 4, 4, 4)
        sb_layout.setSpacing(6)

        lbl_title = QLabel("<b>Gráficos visibles</b>")
        sb_layout.addWidget(lbl_title)

        for key in self._GRAPH_KEYS:
            cb = QCheckBox(self._GRAPH_LABELS[key])
            cb.setChecked(True)
            cb.stateChanged.connect(self._relayout_plots)
            self._checkboxes[key] = cb
            sb_layout.addWidget(cb)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sb_layout.addWidget(sep)

        # Selector de grupo para ángulos
        sb_layout.addWidget(QLabel("<b>Grupo (ángulos)</b>"))
        self.combo_group = QComboBox()
        self.combo_group.setMaximumWidth(180)
        self.combo_group.currentTextChanged.connect(self._on_group_changed)
        sb_layout.addWidget(self.combo_group)

        sb_layout.addStretch()
        root.addWidget(sidebar)

        # ── Área derecha: scroll + grilla dinámica ────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._grid_container = QWidget()
        self._grid = QGridLayout(self._grid_container)
        self._grid.setSpacing(6)
        self._scroll.setWidget(self._grid_container)

        root.addWidget(self._scroll, stretch=1)

        # ── Crear los seis PlotWidgets ─────────────────────────────────────────
        self.plot_angle = pg.PlotWidget(title="Ángulo por motor (°)")
        self.plot_angle.setLabel("left",   "Ángulo",      units="°")
        self.plot_angle.setLabel("bottom", "Tiempo",      units="s")
        self.plot_angle.showGrid(x=True, y=True, alpha=0.3)

        self.plot_temp = pg.PlotWidget(title="Temperatura — todos los motores (°C)")
        self.plot_temp.setLabel("left",   "Temperatura",  units="°C")
        self.plot_temp.setLabel("bottom", "Tiempo",       units="s")
        self.plot_temp.showGrid(x=True, y=True, alpha=0.3)

        self.plot_current = pg.PlotWidget(
            title="Corriente del sistema (A) — picos = esfuerzo mecánico"
        )
        self.plot_current.setLabel("left",   "Corriente", units="A")
        self.plot_current.setLabel("bottom", "Tiempo",    units="s")
        self.plot_current.showGrid(x=True, y=True, alpha=0.3)

        self.plot_voltage = pg.PlotWidget(
            title="Tensión del sistema (V) — caídas = alta demanda"
        )
        self.plot_voltage.setLabel("left",   "Tensión",   units="V")
        self.plot_voltage.setLabel("bottom", "Tiempo",    units="s")
        self.plot_voltage.showGrid(x=True, y=True, alpha=0.3)

        self.plot_soc = pg.PlotWidget(title="Carga de batería (%)")
        self.plot_soc.setLabel("left",   "SOC",    units="%")
        self.plot_soc.setLabel("bottom", "Tiempo", units="s")
        self.plot_soc.setYRange(0, 100)
        self.plot_soc.showGrid(x=True, y=True, alpha=0.3)

        self.plot_cells = pg.PlotWidget(title="Tensión de celdas (mV) — balance de batería")
        self.plot_cells.setLabel("left",   "Tensión", units="mV")
        self.plot_cells.setLabel("bottom", "Tiempo",  units="s")
        self.plot_cells.showGrid(x=True, y=True, alpha=0.3)

        self._plot_widgets = {
            "angle":   self.plot_angle,
            "temp":    self.plot_temp,
            "current": self.plot_current,
            "voltage": self.plot_voltage,
            "soc":     self.plot_soc,
            "cells":   self.plot_cells,
        }

        # Altura mínima por gráfico
        for pw in self._plot_widgets.values():
            pw.setMinimumHeight(220)

        # Colocar los gráficos por primera vez
        self._relayout_plots()

    # ── Relayout dinámico ─────────────────────────────────────────────────────

    def _relayout_plots(self):
        """Quita todos los widgets del grid y vuelve a colocar solo los visibles."""
        # Sacar todos del grid sin destruirlos
        for key, pw in self._plot_widgets.items():
            pw.setParent(None)

        visible_keys = [k for k in self._GRAPH_KEYS if self._checkboxes[k].isChecked()]

        COLS = 2
        for pos, key in enumerate(visible_keys):
            row = pos // COLS
            col = pos % COLS
            self._grid.addWidget(self._plot_widgets[key], row, col)
            self._plot_widgets[key].show()

        # Si el número de visibles es impar, hacemos que el último ocupe 2 columnas
        if len(visible_keys) % 2 == 1 and visible_keys:
            last_key = visible_keys[-1]
            last_row = (len(visible_keys) - 1) // COLS
            self._grid.addWidget(self._plot_widgets[last_key], last_row, 0, 1, 2)

    # ── Inicialización de curvas por robot ────────────────────────────────────

    def setup_motors(self, robot_type: str):
        """Inicializa buffers y curvas para el robot conectado."""
        joint_map = get_joint_map(robot_type)
        num       = get_num_motors(robot_type)

        self._motor_info.clear()
        self._motor_data.clear()
        self._times.clear()
        self._time_start = None
        self._angle_curves.clear()
        self._temp_curves.clear()
        self._power_a_buf.clear()
        self._power_v_buf.clear()
        self._bms_soc_buf.clear()
        self._cell_vol_bufs.clear()
        self._cell_curves.clear()

        groups = []
        for idx in range(num):
            info = joint_map.get(idx, {"name": f"Motor_{idx}", "group": "Otro"})
            self._motor_info[idx] = info
            if info["group"] not in groups:
                groups.append(info["group"])
            self._motor_data[idx] = {
                "q_deg":       deque(maxlen=self.HISTORY),
                "temperature": deque(maxlen=self.HISTORY),
            }

        # Temperatura: una curva por motor
        self.plot_temp.clear()
        self.plot_temp.addLine(
            y=40, pen=pg.mkPen(color=(200, 150, 0), width=1,
                               style=Qt.PenStyle.DashLine),
        )
        self.plot_temp.addLine(
            y=60, pen=pg.mkPen(color=(200, 0, 0), width=1,
                               style=Qt.PenStyle.DashLine),
        )
        self.plot_temp.addLegend(offset=(10, 10))
        for idx in range(num):
            color = _MOTOR_COLORS[idx % len(_MOTOR_COLORS)]
            curve = self.plot_temp.plot(
                pen=pg.mkPen(color, width=2),
                name=self._motor_info[idx]["name"],
            )
            self._temp_curves[idx] = curve

        # Corriente
        self.plot_current.clear()
        self._curve_current = self.plot_current.plot(
            pen=pg.mkPen("#1e88e5", width=2), name="Corriente (A)"
        )
        self.plot_current.addLine(
            y=1.5, pen=pg.mkPen(color=(150, 150, 150), width=1,
                                style=Qt.PenStyle.DashLine)
        )

        # Tensión
        self.plot_voltage.clear()
        self._curve_voltage = self.plot_voltage.plot(
            pen=pg.mkPen("#e53935", width=2), name="Tensión (V)"
        )
        self.plot_voltage.addLine(
            y=27.5, pen=pg.mkPen(color=(150, 150, 150), width=1,
                                 style=Qt.PenStyle.DashLine)
        )

        # SOC
        self.plot_soc.clear()
        self._curve_soc = self.plot_soc.plot(
            pen=pg.mkPen("#43a047", width=2), name="SOC (%)"
        )
        self.plot_soc.addLine(
            y=20, pen=pg.mkPen(color=(200, 0, 0), width=1,
                               style=Qt.PenStyle.DashLine)
        )

        # Celdas
        _cell_colors = ["#e53935", "#1e88e5", "#43a047",
                        "#fb8c00", "#8e24aa", "#00acc1"]
        self.plot_cells.clear()
        self.plot_cells.addLegend(offset=(10, 10))
        self.plot_cells.addLine(
            y=3500, pen=pg.mkPen(color=(150, 150, 150), width=1,
                                 style=Qt.PenStyle.DashLine)
        )
        for i in range(6):
            self._cell_vol_bufs[i] = deque(maxlen=self.HISTORY)
            curve = self.plot_cells.plot(
                pen=pg.mkPen(_cell_colors[i % len(_cell_colors)], width=2),
                name=f"Celda {i + 1}",
            )
            self._cell_curves[i] = curve

        # Ángulo: combo de grupos
        self.combo_group.blockSignals(True)
        self.combo_group.clear()
        self.combo_group.addItems(groups)
        self.combo_group.blockSignals(False)
        if groups:
            self._on_group_changed(groups[0])

    # ── Cambio de grupo en ángulos ────────────────────────────────────────────

    def _on_group_changed(self, group_name: str):
        self.plot_angle.clear()
        self._angle_curves.clear()

        colors = ["#e53935", "#1e88e5", "#43a047", "#fb8c00", "#8e24aa", "#00acc1"]
        self.plot_angle.addLegend(offset=(10, 10))
        i = 0
        for idx, info in self._motor_info.items():
            if info["group"] == group_name:
                curve = self.plot_angle.plot(
                    pen=pg.mkPen(colors[i % len(colors)], width=2),
                    name=info["name"],
                )
                self._angle_curves[idx] = curve
                i += 1

        t_arr = list(self._times)
        for idx, curve in self._angle_curves.items():
            data = list(self._motor_data[idx]["q_deg"])
            n = min(len(t_arr), len(data))
            if n > 0:
                curve.setData(t_arr[-n:], data[-n:])

    # ── Actualización de datos ────────────────────────────────────────────────

    def update_data(self, packet: dict):
        if self._time_start is None:
            self._time_start = packet["timestamp"]
        t = packet["timestamp"] - self._time_start
        self._times.append(t)

        for motor in packet["motors"]:
            idx = motor["index"]
            if idx in self._motor_data:
                self._motor_data[idx]["q_deg"].append(motor["q_deg"])
                self._motor_data[idx]["temperature"].append(motor["temperature"])

        self._power_a_buf.append(packet["power_a"])
        self._power_v_buf.append(packet["power_v"])

        bms = packet.get("bms", {})
        self._bms_soc_buf.append(bms.get("soc", 0))
        for i, mv in enumerate(bms.get("cell_vol", [])):
            if i not in self._cell_vol_bufs:
                self._cell_vol_bufs[i] = deque(maxlen=self.HISTORY)
            self._cell_vol_bufs[i].append(mv)

        t_arr = list(self._times)

        for idx, curve in self._angle_curves.items():
            data = list(self._motor_data[idx]["q_deg"])
            n = min(len(t_arr), len(data))
            if n > 0:
                curve.setData(t_arr[-n:], data[-n:])

        for idx, curve in self._temp_curves.items():
            data = list(self._motor_data[idx]["temperature"])
            n = min(len(t_arr), len(data))
            if n > 0:
                curve.setData(t_arr[-n:], data[-n:])

        if self._curve_current is not None:
            data_a = list(self._power_a_buf)
            n = min(len(t_arr), len(data_a))
            if n > 0:
                self._curve_current.setData(t_arr[-n:], data_a[-n:])

        if self._curve_voltage is not None:
            data_v = list(self._power_v_buf)
            n = min(len(t_arr), len(data_v))
            if n > 0:
                self._curve_voltage.setData(t_arr[-n:], data_v[-n:])

        if self._curve_soc is not None:
            data_soc = list(self._bms_soc_buf)
            n = min(len(t_arr), len(data_soc))
            if n > 0:
                self._curve_soc.setData(t_arr[-n:], data_soc[-n:])

        for i, curve in self._cell_curves.items():
            if i in self._cell_vol_bufs:
                data_c = list(self._cell_vol_bufs[i])
                n = min(len(t_arr), len(data_c))
                if n > 0:
                    curve.setData(t_arr[-n:], data_c[-n:])

    # ── Limpiar ───────────────────────────────────────────────────────────────

    def clear(self):
        self._time_start = None
        self._times.clear()
        self._power_a_buf.clear()
        self._power_v_buf.clear()
        self._bms_soc_buf.clear()
        for buf in self._motor_data.values():
            buf["q_deg"].clear()
            buf["temperature"].clear()
        for curve in self._angle_curves.values():
            curve.setData([], [])
        for curve in self._temp_curves.values():
            curve.setData([], [])
        if self._curve_current is not None:
            self._curve_current.setData([], [])
        if self._curve_voltage is not None:
            self._curve_voltage.setData([], [])
        if self._curve_soc is not None:
            self._curve_soc.setData([], [])
        for buf in self._cell_vol_bufs.values():
            buf.clear()
        for curve in self._cell_curves.values():
            curve.setData([], [])


# ── CompareDialog ───────────────────────────────────────────────────────────────

class CompareDialog(QDialog):
    """Muestra una tabla con los ángulos de todos los motores en cada captura."""

    def __init__(self, history: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Comparar capturas")
        self.setMinimumSize(960, 520)
        self._history = history
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(
            "Ángulo (°) por motor en cada captura.  "
            "Celdas en amarillo: diferencia >10° respecto a la primera captura.  "
            "En rojo: diferencia >30°."
        ))

        if not self._history:
            layout.addWidget(QLabel("No hay capturas guardadas."))
            btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            btns.rejected.connect(self.accept)
            layout.addWidget(btns)
            return

        first     = self._history[0]
        motor_ids = [(m["index"], m["name"], m["group"]) for m in first["motors"]]
        n_snaps   = len(self._history)

        table = QTableWidget(len(motor_ids), n_snaps + 2)
        headers = ["Grupo", "Motor"] + [
            datetime.fromtimestamp(s["timestamp"]).strftime("%H:%M:%S")
            for s in self._history
        ]
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)

        for row, (idx, name, group) in enumerate(motor_ids):
            table.setItem(row, 0, QTableWidgetItem(group))
            table.setItem(row, 1, QTableWidgetItem(name))

            base_angle = None
            for col, snap in enumerate(self._history):
                m_data = next((m for m in snap["motors"] if m["index"] == idx), None)
                if m_data is None:
                    table.setItem(row, col + 2, QTableWidgetItem("—"))
                    continue

                angle = m_data["q_deg"]
                if base_angle is None:
                    base_angle = angle

                item = QTableWidgetItem(f"{angle:.2f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                delta = abs(angle - base_angle) if base_angle is not None else 0
                if delta > 30:
                    item.setBackground(QColor(255, 180, 180))
                elif delta > 10:
                    item.setBackground(QColor(255, 240, 150))

                table.setItem(row, col + 2, item)

        layout.addWidget(table)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(self.accept)
        layout.addWidget(btns)


# ── SensorLabel ─────────────────────────────────────────────────────────────────

class SensorLabel(QLabel):
    """Label con estilo para mostrar un valor de sensor."""
    def __init__(self, title, unit=""):
        super().__init__()
        self.title = title
        self.unit  = unit
        self.set_value("—")

    def set_value(self, value):
        self.setText(f"{self.title}: {value} {self.unit}")


# ── MotorMonitorWindow ──────────────────────────────────────────────────────────

class MotorMonitorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Unitree Motor Monitor — Go2 / G1 EDU")
        self.setMinimumSize(1200, 860)

        self.reader      = None
        self.latest_data = None
        self.history: list = []

        self._build_ui()

    # ── Construcción de la UI ──────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # ── Conexión ──
        conn_group  = QGroupBox("Conexión")
        conn_layout = QHBoxLayout(conn_group)

        conn_layout.addWidget(QLabel("Robot:"))
        self.combo_robot = QComboBox()
        self.combo_robot.addItems(["Go2", "G1"])
        conn_layout.addWidget(self.combo_robot)

        conn_layout.addWidget(QLabel("Interfaz de red:"))
        self.combo_iface = QComboBox()
        self.combo_iface.setMinimumWidth(200)
        self._populate_interfaces()
        conn_layout.addWidget(self.combo_iface)

        self.btn_refresh = QPushButton("Actualizar")
        self.btn_refresh.clicked.connect(self._populate_interfaces)
        conn_layout.addWidget(self.btn_refresh)

        self.btn_connect = QPushButton("Conectar")
        self.btn_connect.clicked.connect(self._on_connect)
        conn_layout.addWidget(self.btn_connect)

        self.btn_disconnect = QPushButton("Desconectar")
        self.btn_disconnect.clicked.connect(self._on_disconnect)
        self.btn_disconnect.setEnabled(False)
        conn_layout.addWidget(self.btn_disconnect)

        conn_layout.addWidget(QLabel("|"))

        self.btn_demo = QPushButton("Modo Demo")
        self.btn_demo.clicked.connect(self._on_demo)
        conn_layout.addWidget(self.btn_demo)

        conn_layout.addWidget(QLabel("Escenario:"))
        self.combo_scenario = QComboBox()
        self.combo_scenario.addItems(["Caminando", "Parado", "Trote", "Motor Recalentado"])
        conn_layout.addWidget(self.combo_scenario)

        conn_layout.addStretch()
        layout.addWidget(conn_group)

        # ── Banner de alertas de temperatura (oculto por defecto) ──
        self.alert_label = QLabel()
        self.alert_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.alert_label.setStyleSheet(
            "font-weight: bold; padding: 4px 8px; border-radius: 4px;"
        )
        self.alert_label.hide()
        layout.addWidget(self.alert_label)

        # ── Sensores ──
        sensors_layout = QHBoxLayout()

        energy_group = QGroupBox("Energía")
        eg = QGridLayout(energy_group)
        self.lbl_voltage = SensorLabel("Voltaje",  "V")
        self.lbl_current = SensorLabel("Corriente","A")
        self.lbl_power   = SensorLabel("Potencia", "W")
        eg.addWidget(self.lbl_voltage, 0, 0)
        eg.addWidget(self.lbl_current, 1, 0)
        eg.addWidget(self.lbl_power,   2, 0)
        sensors_layout.addWidget(energy_group)

        bms_group = QGroupBox("Batería")
        bg = QGridLayout(bms_group)
        self.lbl_soc        = SensorLabel("Carga",        "%")
        self.lbl_bms_current= SensorLabel("Corriente BMS","mA")
        self.lbl_bms_temp   = SensorLabel("Temp NTC",     "")
        self.lbl_bms_cycle  = SensorLabel("Ciclos",       "")
        self.lbl_bms_cells  = SensorLabel("Celdas",       "mV")
        bg.addWidget(self.lbl_soc,         0, 0)
        bg.addWidget(self.lbl_bms_current, 1, 0)
        bg.addWidget(self.lbl_bms_temp,    2, 0)
        bg.addWidget(self.lbl_bms_cycle,   3, 0)
        bg.addWidget(self.lbl_bms_cells,   4, 0)
        sensors_layout.addWidget(bms_group)

        imu_group = QGroupBox("IMU — Orientación")
        ig = QGridLayout(imu_group)
        self.lbl_roll  = SensorLabel("Roll",       "°")
        self.lbl_pitch = SensorLabel("Pitch",      "°")
        self.lbl_yaw   = SensorLabel("Yaw",        "°")
        self.lbl_accel = SensorLabel("Aceleración","m/s²")
        self.lbl_gyro  = SensorLabel("Giroscopio", "rad/s")
        ig.addWidget(self.lbl_roll,  0, 0)
        ig.addWidget(self.lbl_pitch, 0, 1)
        ig.addWidget(self.lbl_yaw,   0, 2)
        ig.addWidget(self.lbl_accel, 1, 0, 1, 2)
        ig.addWidget(self.lbl_gyro,  1, 2)
        sensors_layout.addWidget(imu_group)

        foot_group = QGroupBox("Fuerza en patas")
        fg = QGridLayout(foot_group)
        self.lbl_ff_fr = SensorLabel("FR","")
        self.lbl_ff_fl = SensorLabel("FL","")
        self.lbl_ff_rr = SensorLabel("RR","")
        self.lbl_ff_rl = SensorLabel("RL","")
        fg.addWidget(self.lbl_ff_fr, 0, 0)
        fg.addWidget(self.lbl_ff_fl, 0, 1)
        fg.addWidget(self.lbl_ff_rr, 1, 0)
        fg.addWidget(self.lbl_ff_rl, 1, 1)
        sensors_layout.addWidget(foot_group)

        layout.addLayout(sensors_layout)

        # ── Captura / exportación ──
        cap_layout = QHBoxLayout()

        self.btn_snapshot = QPushButton("Capturar dato actual")
        self.btn_snapshot.clicked.connect(self._on_snapshot)
        self.btn_snapshot.setEnabled(False)
        cap_layout.addWidget(self.btn_snapshot)

        self.lbl_snapcount = QLabel("Capturas: 0")
        cap_layout.addWidget(self.lbl_snapcount)

        self.btn_compare = QPushButton("Comparar capturas")
        self.btn_compare.clicked.connect(self._on_compare)
        self.btn_compare.setEnabled(False)
        cap_layout.addWidget(self.btn_compare)

        self.btn_export = QPushButton("Exportar CSV")
        self.btn_export.clicked.connect(self._on_export_csv)
        self.btn_export.setEnabled(False)
        cap_layout.addWidget(self.btn_export)

        cap_layout.addStretch()
        layout.addLayout(cap_layout)

        # ── Tabs: Tabla / Gráficos ──
        self.tabs = QTabWidget()

        table_widget  = QWidget()
        table_layout  = QVBoxLayout(table_widget)
        table_layout.setContentsMargins(0, 4, 0, 0)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Grupo", "Motor", "Ángulo (°)",
            "Vel. (rad/s)", "Torque (N·m)", "Temp (°C)", "Índice",
        ])
        hdr = self.table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in range(2, 7):
            hdr.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        table_layout.addWidget(self.table)
        self.tabs.addTab(table_widget, "Tabla de motores")

        self.graph_panel = GraphPanel()
        self.tabs.addTab(self.graph_panel, "Graficos en tiempo real")

        layout.addWidget(self.tabs)

        # ── Status bar ──
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Desconectado — Selecciona el robot e interfaz de red")

    # ── Interfaces de red ──────────────────────────────────────────────────────

    def _populate_interfaces(self):
        self.combo_iface.clear()
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["ipconfig"], capture_output=True, text=True, timeout=5,
                )
                current_name = None
                for line in result.stdout.split("\n"):
                    line = line.strip()
                    if line.endswith(":") and ("adapter" in line.lower() or "adaptador" in line.lower()):
                        current_name = line.replace(":", "").strip()
                        for prefix in [
                            "Ethernet adapter ", "Wireless LAN adapter ",
                            "Adaptador de Ethernet ", "Adaptador de LAN inalámbrica ",
                        ]:
                            if current_name.startswith(prefix):
                                current_name = current_name[len(prefix):]
                    elif current_name and ("IPv4" in line or "Dirección IPv4" in line):
                        self.combo_iface.addItem(current_name)
                        current_name = None
            else:
                result = subprocess.run(
                    ["ip", "-o", "link", "show"],
                    capture_output=True, text=True, timeout=5,
                )
                for line in result.stdout.strip().split("\n"):
                    parts = line.split(": ")
                    if len(parts) >= 2:
                        name = parts[1].split("@")[0]
                        if name != "lo":
                            self.combo_iface.addItem(name)
        except Exception:
            self.combo_iface.addItem("eth0")

        if self.combo_iface.count() == 0:
            self.combo_iface.addItem("No se detectaron interfaces")

    # ── Conexión ──────────────────────────────────────────────────────────────

    def _on_demo(self):
        robot    = self.combo_robot.currentText().lower()
        scenario = self.combo_scenario.currentText().lower()
        self.status.showMessage(
            f"Modo demo — {robot.upper()} | Escenario: {self.combo_scenario.currentText()}"
        )
        self.btn_connect.setEnabled(False)
        self.btn_demo.setEnabled(False)
        self.combo_scenario.setEnabled(False)
        self._setup_table(robot)
        self.reader = DDSReader(robot, "", demo_mode=True, scenario=scenario)
        self._connect_reader()
        self.reader.start()

    def _on_connect(self):
        robot = self.combo_robot.currentText().lower()
        iface = self.combo_iface.currentText().strip()
        if not iface:
            QMessageBox.warning(self, "Error", "Selecciona la interfaz de red")
            return
        self.status.showMessage(f"Conectando a {robot.upper()} por {iface}...")
        self.btn_connect.setEnabled(False)
        self._setup_table(robot)
        self.reader = DDSReader(robot, iface)
        self._connect_reader()
        self.reader.start()

    def _connect_reader(self):
        self.reader.data_received.connect(self._on_data)
        self.reader.error_occurred.connect(self._on_error)
        self.reader.connected.connect(self._on_connected)

    def _on_connected(self):
        self.status.showMessage("Conectado — Recibiendo datos...")
        self.btn_disconnect.setEnabled(True)
        self.btn_export.setEnabled(True)
        self.btn_snapshot.setEnabled(True)
        self.combo_robot.setEnabled(False)
        self.combo_iface.setEnabled(False)

    def _on_disconnect(self):
        if self.reader:
            self.reader.stop()
            self.reader = None

        self.btn_connect.setEnabled(True)
        self.btn_demo.setEnabled(True)
        self.btn_disconnect.setEnabled(False)
        self.btn_snapshot.setEnabled(False)
        self.combo_robot.setEnabled(True)
        self.combo_iface.setEnabled(True)
        self.combo_scenario.setEnabled(True)
        self.alert_label.hide()
        self.graph_panel.clear()
        self.status.showMessage("Desconectado")

    def _on_error(self, msg):
        self.btn_connect.setEnabled(True)
        self.btn_demo.setEnabled(True)
        self.combo_scenario.setEnabled(True)
        self.status.showMessage(f"Error: {msg}")
        QMessageBox.critical(self, "Error de conexión", msg)

    # ── Tabla ─────────────────────────────────────────────────────────────────

    def _setup_table(self, robot_type: str):
        joint_map = get_joint_map(robot_type)
        num       = get_num_motors(robot_type)
        self.table.setRowCount(num)

        for idx in range(num):
            info = joint_map.get(idx, {"name": f"Motor_{idx}", "group": "Otro"})

            self.table.setItem(idx, 0, QTableWidgetItem(info["group"]))

            name_item = QTableWidgetItem(info["name"])
            tip = _joint_tooltip(info["name"])
            if tip:
                name_item.setToolTip(tip)
            self.table.setItem(idx, 1, name_item)

            for col in range(2, 6):
                self.table.setItem(idx, col, QTableWidgetItem("—"))
            self.table.setItem(idx, 6, QTableWidgetItem(str(idx)))

        self.graph_panel.setup_motors(robot_type)

    # ── Actualización de datos ─────────────────────────────────────────────────

    def _on_data(self, packet: dict):
        self.latest_data = packet

        # Energía
        v = packet["power_v"]
        a = packet["power_a"]
        self.lbl_voltage.set_value(f"{v:.1f}")
        self.lbl_current.set_value(f"{a:.2f}")
        self.lbl_power.set_value(f"{v * a:.1f}")

        # Batería
        bms   = packet.get("bms", {})
        ntc   = bms.get("mcu_ntc", [])
        cells = bms.get("cell_vol", [])
        self.lbl_soc.set_value(bms.get("soc", "—"))
        self.lbl_bms_current.set_value(bms.get("current", "—"))
        self.lbl_bms_cycle.set_value(bms.get("cycle", "—"))
        self.lbl_bms_temp.set_value(", ".join(str(t) for t in ntc)   if ntc   else "—")
        self.lbl_bms_cells.set_value(", ".join(str(c) for c in cells) if cells else "—")

        # IMU
        imu   = packet.get("imu", {})
        rpy   = imu.get("rpy_deg",      [0, 0, 0])
        accel = imu.get("accelerometer",[0, 0, 0])
        gyro  = imu.get("gyroscope",    [0, 0, 0])
        self.lbl_roll.set_value(f"{rpy[0]:.1f}")
        self.lbl_pitch.set_value(f"{rpy[1]:.1f}")
        self.lbl_yaw.set_value(f"{rpy[2]:.1f}")
        self.lbl_accel.set_value(f"x:{accel[0]:.2f} y:{accel[1]:.2f} z:{accel[2]:.2f}")
        self.lbl_gyro.set_value(f"x:{gyro[0]:.3f} y:{gyro[1]:.3f} z:{gyro[2]:.3f}")

        # Fuerza patas
        ff = packet.get("foot_force", [0, 0, 0, 0])
        self.lbl_ff_fr.set_value(ff[0])
        self.lbl_ff_fl.set_value(ff[1])
        self.lbl_ff_rr.set_value(ff[2])
        self.lbl_ff_rl.set_value(ff[3])

        # Tabla de motores + alertas de temperatura
        hot_motors  = []
        warm_motors = []

        for motor in packet["motors"]:
            row  = motor["index"]
            temp = motor["temperature"]

            self.table.item(row, 2).setText(f"{motor['q_deg']:.2f}")
            self.table.item(row, 3).setText(f"{motor['dq']:.4f}")
            self.table.item(row, 4).setText(f"{motor['tau_est']:.4f}")

            temp_item = self.table.item(row, 5)
            temp_item.setText(str(temp))
            if temp >= 60:
                temp_item.setBackground(QColor(255, 100, 100))
                hot_motors.append(motor["name"])
            elif temp >= 40:
                temp_item.setBackground(QColor(255, 255, 100))
                warm_motors.append(motor["name"])
            else:
                temp_item.setBackground(QColor(100, 220, 100))

        # Banner de alertas
        if hot_motors:
            self.alert_label.setStyleSheet(
                "background-color: #c62828; color: white; "
                "font-weight: bold; padding: 4px 8px; border-radius: 4px;"
            )
            self.alert_label.setText(
                f"ALERTA — TEMPERATURA CRITICA (>=60 C): {', '.join(hot_motors)}"
            )
            self.alert_label.show()
        elif warm_motors:
            self.alert_label.setStyleSheet(
                "background-color: #e65100; color: white; "
                "font-weight: bold; padding: 4px 8px; border-radius: 4px;"
            )
            self.alert_label.setText(
                f"AVISO — Temperatura elevada (>=40 C): {', '.join(warm_motors)}"
            )
            self.alert_label.show()
        else:
            self.alert_label.hide()

        # Gráficos (siempre actualizamos el buffer; pyqtgraph no redibuja si no es visible)
        self.graph_panel.update_data(packet)

    # ── Capturas y exportación ─────────────────────────────────────────────────

    def _on_snapshot(self):
        if self.latest_data:
            self.history.append(self.latest_data)
            count = len(self.history)
            self.lbl_snapcount.setText(f"Capturas: {count}")
            self.status.showMessage(f"Captura #{count} guardada")
            if count >= 2:
                self.btn_compare.setEnabled(True)

    def _on_compare(self):
        dlg = CompareDialog(self.history, parent=self)
        dlg.exec()

    def _on_export_csv(self):
        if not self.history:
            QMessageBox.information(
                self, "Sin datos",
                "Usa 'Capturar dato actual' para guardar mediciones antes de exportar.",
            )
            return

        default_name = f"motores_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar CSV", default_name, "CSV (*.csv)"
        )
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Captura", "Timestamp", "Robot",
                "Voltaje_V", "Corriente_A", "Potencia_W",
                "Bateria_%", "Bateria_Temp_C", "Bateria_Ciclos",
                "Roll_deg", "Pitch_deg", "Yaw_deg",
                "Acel_X", "Acel_Y", "Acel_Z",
                "Gyro_X", "Gyro_Y", "Gyro_Z",
                "Fuerza_FR", "Fuerza_FL", "Fuerza_RR", "Fuerza_RL",
                "Grupo", "Motor", "Indice",
                "Angulo_deg", "Vel_rad_s", "Acel_rad_s2",
                "Torque_Nm", "Temp_C",
            ])

            for i, snap in enumerate(self.history, 1):
                ts    = datetime.fromtimestamp(snap["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                imu   = snap.get("imu", {})
                rpy   = imu.get("rpy_deg",       [0, 0, 0])
                accel = imu.get("accelerometer",  [0, 0, 0])
                gyro  = imu.get("gyroscope",      [0, 0, 0])
                ff    = snap.get("foot_force",    [0, 0, 0, 0])
                bms   = snap.get("bms", {})
                v     = snap["power_v"]
                a     = snap["power_a"]

                for m in snap["motors"]:
                    writer.writerow([
                        i, ts, snap["robot"],
                        v, a, round(v * a, 1),
                        bms.get("soc", 0), bms.get("current", 0), bms.get("cycle", 0),
                        rpy[0], rpy[1], rpy[2],
                        accel[0], accel[1], accel[2],
                        gyro[0],  gyro[1],  gyro[2],
                        ff[0], ff[1], ff[2], ff[3],
                        m["group"], m["name"], m["index"],
                        m["q_deg"], m["dq"], m["ddq"],
                        m["tau_est"], m["temperature"],
                    ])

        self.status.showMessage(f"CSV exportado: {path}")
        QMessageBox.information(self, "Exportado", f"Archivo guardado en:\n{path}")

    def closeEvent(self, event):
        self._on_disconnect()
        event.accept()
