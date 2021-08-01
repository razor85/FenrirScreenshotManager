from PyQt5.QtWidgets import QFrame
from PyQt5.QtCore import Qt

class TitleFrame(QFrame):
  def __init__(self, p):
    super().__init__(p)
    self.window = None

  def setWindow(self, window):
    self.window = window
  
  def mousePressEvent(self, event):
    if event.button() == Qt.LeftButton:
      self.window.moving = True
      self.window.offset = event.pos()

  def mouseMoveEvent(self, event):
    if self.window.moving:
      self.window.move(event.globalPos() - self.window.offset)
