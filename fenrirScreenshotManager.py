from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog, QLabel, QGraphicsDropShadowEffect
from PyQt5.QtGui import QColor, QIcon, QPixmap
from PyQt5.QtCore import pyqtSignal, QTimer
from PyQt5 import uic
from PIL import Image
from pathlib import Path
from libs.FlowLayout import FlowLayout
import libs.DiskUtil as disk_util
import io
import sys

class CoverLabel(QLabel):
  clicked = pyqtSignal()
  def __init__(self, cover_url):
    super().__init__()
    self.cover_url = cover_url

  def mousePressEvent(self, event):
    self.clicked.emit()

results_window_ui = 'ui/results.ui'
results_form, results_base = uic.loadUiType(results_window_ui)

class ResultsWindow(results_base, results_form):
  def __init__(self, game_name):
    super(results_base, self).__init__()
    self.setupUi(self)
    self.setEvents()
    self.flowLayout = FlowLayout()
    self.flowWidget = QWidget()
    self.flowWidget.setLayout(self.flowLayout)
    self.resultsScrollArea.setWidget(self.flowWidget)
    self.searchEdit.setText('Sega Saturn {}'.format(game_name))
    self.labels = []
    self.active_cover = None
    self.timer = None
    self.search()

  def setEvents(self):
    self.searchButton.clicked.connect(self.search)

  def clearLayout(self):
    for i in reversed(range(self.flowLayout.count())):
      item = self.flowLayout.takeAt(i)
      if item and item.widget():
        item.widget().deleteLater()

  def resetLabel(self, label):
    label.graphicsEffect().setColor(QColor(0, 0, 0))
    label.setStyleSheet("border: 3px solid black;")

  def unselectLabels(self):
    for label in self.labels:
      self.resetLabel(label)

  def coverClicked(self, label):
    self.unselectLabels()
    self.active_cover = label.cover_url
    label.graphicsEffect().setColor(QColor(255, 0, 0))
    label.setStyleSheet("border: 3px solid red;")

  def setComponentsState(self, state):
    self.searchEdit.setEnabled(state)
    self.maxResultsEdit.setEnabled(state)
    self.searchButton.setEnabled(state)
    self.resultsScrollArea.setEnabled(state)
    self.buttonBox.setEnabled(state)

  def search(self):
    self.active_cover = None
    self.labels = []
    self.clearLayout()
    self.setComponentsState(False)
    self.searchQuery = disk_util.QueryResults(self.searchEdit.text(),
                                              int(self.maxResultsEdit.text()))

    self.timer = QTimer()
    self.timer.timeout.connect(self.timerEvent)
    self.timer.start(1000)

  def abortTimer(self):
    if self.timer:
      self.timer.stop()
      self.timer = None

  def timerEvent(self):
    if not self.searchQuery:
      self.abortTimer()

    if self.searchQuery.done():
      self.abortTimer()
      self.searchQuery = None
      self.displaySearchResults()

  def displaySearchResults(self):
    self.setComponentsState(True)
    items = disk_util.getTempFolder().glob('*.jpg')
    for filename in items:
      new_label = CoverLabel(filename)
      new_label.setPixmap(QPixmap(str(filename)).scaled(256, 192))
      new_label.setStyleSheet("border: 3px solid black;")
      new_label.clicked.connect(lambda l=new_label: self.coverClicked(l))
      shadow_effect = QGraphicsDropShadowEffect()
      shadow_effect.setOffset(3, 3)
      shadow_effect.setBlurRadius(5)
      shadow_effect.setColor(QColor(0, 0, 0))
      new_label.setGraphicsEffect(shadow_effect)
      self.resetLabel(new_label)
      self.flowLayout.addWidget(new_label)
      self.labels.append(new_label)

  def accept(self):
    if self.searchQuery:
      return
    else:
      return super().accept()

  def reject(self):
    if self.searchQuery:
      return
    else:
      return super().reject()
      
  def done(self, res):
    if self.searchQuery:
      return
    else:
      return super().done(res)

  def exec(self):
    if super().exec():
      return self.active_cover
    else:
      return None

main_window_ui = 'ui/main.ui'
main_form, main_base = uic.loadUiType(main_window_ui)

class MainWindow(main_base, main_form):
  def __init__(self):
    super(main_base, self).__init__()
    self.setupUi(self)
    self.setEvents()
    self.showGamesList()
    self.gameFolderEdit.setText(str(disk_util.getGamesFolder()))
    self.screenshotsEdit.setText(str(disk_util.getScreenshotFolder()))
    shadow_effect = QGraphicsDropShadowEffect()
    shadow_effect.setOffset(2, 2)
    shadow_effect.setBlurRadius(5)
    shadow_effect.setColor(QColor(26, 88, 175))
    self.titleLabel.setGraphicsEffect(shadow_effect)

  def showGamesList(self):
    self.game_list = sorted(disk_util.get_game_list())
    self.gameList.clear()
    self.gameList.addItems(self.game_list)

  def setEvents(self):
    self.gameList.itemSelectionChanged.connect(self.gameSelectionChanged)
    self.gameFolderBrowseButton.clicked.connect(self.browseGamesFolder)
    self.screenshotFolderBrowseButton.clicked.connect(self.browseScreenshotsFolder)
    self.thumbnailDownloadButton.clicked.connect(self.replaceGameCover)

  def setThumbnailToFile(self, filename):
    self.thumbnailLabel.setPixmap(QPixmap(str(filename)).scaled(256, 192))

  def replaceGameCover(self):
    selection = self.gameList.selectedItems()
    if not selection:
      return

    game_name = selection[0].text()
    results = ResultsWindow(disk_util.cleanName(game_name))
    selected_cover = results.exec()
    if selected_cover:
      img = Image.open(selected_cover)
      img = img.resize((128, 96))
      output_name = disk_util.getScreenshotFolder() / Path('{}.jpg'.format(game_name))
      img.save(output_name, 'JPEG', quality=100)
      self.setThumbnailToFile(str(output_name))

  def browseGamesFolder(self):
    new_games = QFileDialog.getExistingDirectory()
    if new_games:
      disk_util.games_folder = Path(new_games)
      screenshot_folder = disk_util.games_folder / Path('screenshots')
      if screenshot_folder.exists():
        disk_util.screenshot_folder = screenshot_folder
        self.screenshotsEdit.setText(str(screenshot_folder))

      self.gameFolderEdit.setText(new_games)
      self.showGamesList()
      self.gameSelectionChanged()

  def browseScreenshotsFolder(self):
    new_screenshot = QFileDialog.getExistingDirectory()
    if new_screenshot:
      disk_util.screenshot_folder = Path(new_screenshot)
      self.screenshotsEdit.setText(new_screenshot)
      self.showGamesList()
      self.gameSelectionChanged()

  def gameSelectionChanged(self):
    selection = self.gameList.selectedItems()
    if not selection:
      return

    game_name = selection[0].text()
    thumbnail_file = disk_util.get_thumbnail(game_name)
    self.setThumbnailToFile(thumbnail_file)

if __name__ == '__main__':
  app = QApplication(sys.argv)
  ex = MainWindow()
  ex.show()
  sys.exit(app.exec_())
