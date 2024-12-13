from PyQt5.QtWidgets import QApplication
from MixerUI import ModernWindow
import sys 
from MixerUI import MainController, SliderWithTooltip, InfoButton, QProgressIndicator, ImageDisplay, ImageViewerWidget

class MainWindow(ModernWindow):
    def __init__(self):
        super().__init__()
        self.buildUI()
        self.controller = MainController(self)  # Set controller after window creation
        


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
