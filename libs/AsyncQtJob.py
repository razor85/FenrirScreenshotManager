from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QTimer
from libs.DiskUtil import AsyncJob

class AsyncQtJob(AsyncJob):
  def __init__(self, func, gui_done, timeout=500):
    super().__init__(func)
    self.gui_done = gui_done
    self.timer = QTimer()
    self.timer.timeout.connect(self.timerEvent)
    self.timer.start(timeout)

  def timerEvent(self):
    try:
      if self.done():
        if self.timer:
          self.timer.stop()
          self.timer = None

        self.gui_done(self)

    except Exception as e:
      QMessageBox.information(None, 'Error', 'Error executing task: {}'.format(str(e)))
      if self.timer:
        self.timer.stop()
        self.timer = None

      self.gui_done(None)


