from pathlib import Path
from PyQt5 import uic
from PyQt5.QtWidgets import (
    QMainWindow,
)

from ament_index_python.packages import (
    get_package_share_directory,
)


class MainWindow(QMainWindow):

    def __init__(self):

        super().__init__()

        package_dir = Path(get_package_share_directory("robot_control_panel"))
        ui_file = package_dir / "ui" / "robot_control_panel.ui"

        uic.loadUi(
            str(ui_file),
            self,
        )

        self.setup_connections()

    def setup_connections(self):

        if hasattr(
            self,
            "btn_home",
        ):
            self.btn_home.clicked.connect(self.on_home)

        if hasattr(
            self,
            "btn_stop",
        ):
            self.btn_stop.clicked.connect(self.on_stop)

    def on_home(self):
        self.lbl_message.setText("HOME command requested")

    def on_stop(self):
        self.lbl_message.setText("STOP command requested")
