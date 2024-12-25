PLOT_STYLE = {
    'axes.labelcolor': 'white',
    'axes.edgecolor': 'white',
    'text.color': 'white',
    'xtick.color': 'white',
    'ytick.color': 'white',
    'grid.color': '#404040',
    'figure.facecolor': '#1e1e1e',
    'axes.facecolor': '#2d2d2d',
}


STYLE_SHEET = """
QMainWindow {
    background-color: #1e1e1e;
    color: #ffffff;
}
QWidget {
    background-color: #1e1e1e;
    color: #ffffff;
}
QGroupBox {
    border: 2px solid #3a3a3a;
    border-radius: 5px;
    margin-top: 1em;
    padding-top: 10px;
    color: #ffffff;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 3px 0 3px;
}
QLabel {
    color: #ffffff;
}
QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #3a3a3a;
    border-radius: 3px;
    color: #ffffff;
    padding: 5px;
}
QPushButton {
    background-color: #0d47a1;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 8px 16px;
    text-align: center;
}
QPushButton:hover {
    background-color: #1565c0;
}
QPushButton:pressed {
    background-color: #0a3d91;
}
QDockWidget {
    border: 1px solid #3a3a3a;
    titlebar-close-icon: url(close.png);
}
QDockWidget::title {
    text-align: left;
    background: #2d2d2d;
    padding-left: 5px;
    height: 25px;
}
QMenuBar {
    background-color: #2d2d2d;
    color: white;
}
QMenuBar::item {
    spacing: 3px;
    padding: 5px 10px;
    background: transparent;
}
QMenuBar::item:selected {
    background: #3a3a3a;
}
"""

STYLE_SHEET += """
QDoubleSpinBox::up-button, QSpinBox::up-button {
    border-radius: 3px;
}
QDoubleSpinBox::down-button, QSpinBox::down-button {
    border-radius: 3px;
}
QToolTip {
    background-color: #2d2d2d;
    color: white;
    border: 1px solid #3a3a3a;
    padding: 5px;
}
QGroupBox {
    background-color: #252525;
    border-radius: 8px;
    margin-top: 1.5em;
}
"""