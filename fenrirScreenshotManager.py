from PyQt5.QtWidgets import (QApplication,
                             QWidget,
                             QFileDialog,
                             QLabel,
                             QGraphicsDropShadowEffect,
                             QMessageBox)

from PyQt5.QtGui import QColor, QIcon, QPixmap, QRegion
from PyQt5.QtCore import pyqtSignal, QTimer, Qt, QRect
from PyQt5 import uic
from PIL import Image
from pathlib import Path
from libs.FlowLayout import FlowLayout
from libs.AsyncQtJob import AsyncQtJob
from libs.TitleFrame import TitleFrame
import libs.DiskUtil as disk_util
import io
import shutil
import sys

stylesheet = None
def getStyleSheet():
  global stylesheet
  if not stylesheet:
    with open('ui/style.css', 'r') as file_ptr:
      stylesheet = file_ptr.read()

  return stylesheet

class CoverLabel(QLabel):
  clicked = pyqtSignal()
  def __init__(self, cover_url):
    super().__init__()
    self.cover_url = cover_url

  def mousePressEvent(self, event):
    self.clicked.emit()

loading_window_ui = 'ui/loading.ui'
loading_form, loading_base = uic.loadUiType(loading_window_ui)

class LoadingWindow(loading_base, loading_form):
  def __init__(self, parent, label='Working...'):
    super(select_folder_base, self).__init__(parent)
    self.setupUi(self)
    self.setStyleSheet(getStyleSheet())
    self.setWindowFlag(Qt.FramelessWindowHint)
    self.progressLabel.setText(label)

  def keyPressEvent(self, event):
    None

select_folder_window_ui = 'ui/selectFolder.ui'
select_folder_form, select_folder_base = uic.loadUiType(select_folder_window_ui)

class SelectFolderWindow(select_folder_base, select_folder_form):
  def __init__(self):
    super(select_folder_base, self).__init__()
    self.setupUi(self)
    self.setStyleSheet(getStyleSheet())
    self.setWindowFlag(Qt.FramelessWindowHint)
    self.setWindowFlag(Qt.WindowCloseButtonHint, False)
    self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
    self.browseButton.clicked.connect(self.browseGamesFolder)

  def browseGamesFolder(self):
    new_games = QFileDialog.getExistingDirectory()
    if new_games:
      self.directoryEdit.setText(new_games)

  def done(self, ret_code):
    path = self.directoryEdit.text()
    screenshots = Path(path) / Path('screenshots')
    if not screenshots.exists() and ret_code != 0:
      msg = 'Invalid SD card path, \'{}\' directory not found. Create it and continue?'
      answer = QMessageBox.question(None, 'Screenshots not found',
                                    msg.format(str(screenshots)),
                                    QMessageBox.Yes | QMessageBox.No)

      if answer == QMessageBox.Yes:
        screenshots.mkdir(parents=True)
        super().done(ret_code)
    else:
      super().done(ret_code)

  def exec(self):
    super().exec()
    return self.directoryEdit.text()

results_window_ui = 'ui/results.ui'
results_form, results_base = uic.loadUiType(results_window_ui)
class ResultsWindow(results_base, results_form):
  def __init__(self, game_name):
    super(results_base, self).__init__()
    self.setupUi(self)
    self.setStyleSheet(getStyleSheet())
    self.setWindowFlag(Qt.FramelessWindowHint)
    self.setEvents()
    self.flowLayout = FlowLayout()
    self.flowWidget = QWidget()
    self.flowWidget.setLayout(self.flowLayout)
    self.flowWidget.setAccessibleName('resultsWidget')
    self.resultsScrollArea.setWidget(self.flowWidget)
    self.searchEdit.setText('Sega Saturn {}'.format(game_name))
    self.labels = []
    self.active_cover = None
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
    label.setStyleSheet("border: 1px solid black;")

  def unselectLabels(self):
    for label in self.labels:
      self.resetLabel(label)

  def coverClicked(self, label):
    self.unselectLabels()
    self.active_cover = label.cover_url
    label.graphicsEffect().setColor(QColor(255, 0, 0))
    label.setStyleSheet("border: 1px solid red;")

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
    def query_func():
      return disk_util._download_thumbnails(self.searchEdit.text(),
                                            int(self.maxResultsEdit.text()))

    self.searchQuery = AsyncQtJob(query_func, self.queryDone)
    self.loading = LoadingWindow(self, 'Searching...')
    self.loading.exec()

  def queryDone(self, query):
    self.loading.close()
    self.loading = None
    if query.done():
      self.searchQuery = None
      self.displaySearchResults()

  def displaySearchResults(self):
    self.setComponentsState(True)
    items = disk_util.getImagesTempFolder().glob('*.jpg')
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
    self.setStyleSheet(getStyleSheet())
    self.setEvents()
    self.verticalLayout.setContentsMargins(10, 10, 10, 10)
    self.setWindowFlag(Qt.FramelessWindowHint)

    shadow_effect = QGraphicsDropShadowEffect()
    shadow_effect.setOffset(2, 2)
    shadow_effect.setBlurRadius(5)
    shadow_effect.setColor(QColor(26, 88, 175))
    self.titleFrame.setWindow(self)
    self.titleLabel.setGraphicsEffect(shadow_effect)
    self.games_directory = SelectFolderWindow().exec()
    if self.games_directory:
      self.games_screenshot_directory = self.games_directory / Path('screenshots')
      disk_util.games_folder = Path(self.games_directory)
      self.copyOriginalScreenshots()
    
    self.configButton.setVisible(False)
    self.loading_window = None
    self.write_images_job = None
    self.showGamesList()

  def setComponentsState(self, state):
    self.thumbnailDownloadButton.setEnabled(state)
    self.thumbnailRemoveButton.setEnabled(state)
    self.thumbnailRestoreButton.setEnabled(state)
    self.gameList.setEnabled(state)
    self.configButton.setEnabled(state)
    self.writeImagesButton.setEnabled(state)
    self.quitButton.setEnabled(state)

  def copyOriginalScreenshots(self):
    temp_directory = disk_util.getScreenshotsTempFolder()
    if temp_directory.exists():
      shutil.rmtree(temp_directory)

    temp_directory.mkdir(parents=True)
    original_files = self.games_screenshot_directory.glob('*.jpg')
    for filename in original_files:
      shutil.copyfile(filename, temp_directory / filename.name)

  def showGamesList(self):
    self.game_list = sorted(disk_util.get_game_list())
    self.gameList.clear()
    self.gameList.addItems(self.game_list)

  def setEvents(self):
    self.gameList.itemSelectionChanged.connect(self.gameSelectionChanged)
    self.thumbnailDownloadButton.clicked.connect(self.replaceGameCover)
    self.thumbnailRestoreButton.clicked.connect(self.restoreGameCover)
    self.thumbnailRemoveButton.clicked.connect(self.removeGameCover)
    self.writeImagesButton.clicked.connect(self.writeImages)
    self.quitButton.clicked.connect(self.close)
      
  def backupScreenshots(self):
    backup_folder = self.games_directory / Path('screenshots_backup')
    count = 0
    while backup_folder.exists():
      backup_folder = self.games_directory / Path('screenshots_backup{}'.format(count))

    backup_folder.mkdir(parents=True)
    original_files = self.games_screenshot_directory.glob('*.jpg')
    for filename in original_files:
      shutil.copyfile(filename, backup_folder / filename.name)

  def writeImagesImpl(self):
    source = disk_util.getScreenshotsTempFolder().glob('*.jpg')
    destination = self.games_screenshot_directory
    for filename in source:
      shutil.copyfile(filename, destination / filename.name)

  def writeImagesDone(self, job):
    self.loading_window.close()
    self.loading_window = None
    self.write_images_job = None
    if job.done():
      QMessageBox.information(self, 'Complete', 'Files copied successfully')
      self.setComponentsState(True)

  def writeImages(self):
    msg = ('This action will write the images to your SD card.' +
           'Do you want a backup of your \'screenshots\' folder?' +
           'If you do, sd:/screenshots_backup will be created') 

    answer = QMessageBox.question(None, 'Backup first?', msg,
                                  QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)

    if answer == QMessageBox.Cancel:
      return
    elif answer == QMessageBox.Yes:
      def writeAll():
        self.backupScreenshots()
        self.writeImagesImpl()
      
      self.write_images_job = AsyncQtJob(writeAll, self.writeImagesDone)
    elif answer == QMessageBox.No:
      self.write_images_job = AsyncQtJob(self.writeImagesImpl, self.writeImagesDone)
      
    self.loading_window = LoadingWindow(self, 'Writing to SD...')
    self.loading_window.show()
    self.setComponentsState(False)

  def setThumbnailToFile(self, filename):
    if filename and filename.exists():
      self.thumbnailLabel.setPixmap(QPixmap(str(filename)).scaled(256, 192))
    else:
      self.thumbnailLabel.setPixmap(QPixmap('ui/notfound.png').scaled(256, 192))
    
  def restoreGameCover(self):
    selection = self.gameList.selectedItems()
    if not selection:
      return

    game_name = selection[0].text()
    source = self.games_screenshot_directory / Path('{}.jpg'.format(game_name))
    destination = disk_util.getScreenshotsTempFolder() / Path('{}.jpg'.format(game_name))
    if source.exists():
      shutil.copy(source, destination)
      self.gameSelectionChanged()

  def removeGameCover(self):
    selection = self.gameList.selectedItems()
    if not selection:
      return

    game_name = selection[0].text()
    filename = disk_util.getScreenshotsTempFolder() / Path('{}.jpg'.format(game_name))
    if filename.exists():
      filename.unlink()
      self.gameSelectionChanged()

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
      output_name = disk_util.getScreenshotsTempFolder() / Path('{}.jpg'.format(game_name))
      img.save(output_name, 'JPEG', quality=100)
      self.setThumbnailToFile(output_name)

  def gameSelectionChanged(self):
    selection = self.gameList.selectedItems()
    self.thumbnailDownloadButton.setEnabled(selection != None)
    self.thumbnailRestoreButton.setEnabled(selection != None)
    self.thumbnailRemoveButton.setEnabled(selection != None)
    if not selection:
      return

    game_name = selection[0].text()
    thumbnail_file = disk_util.get_thumbnail(game_name)
    self.setThumbnailToFile(thumbnail_file)
  
  def done(self, res):
    if self.loading_window or self.write_images_job:
      return
    else:
      return super().done(res)

if __name__ == '__main__':
  app = QApplication(sys.argv)
  ex = MainWindow()
  ex.show()
  if ex.games_directory:
    sys.exit(app.exec_())
