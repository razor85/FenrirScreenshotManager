import libs.DuckDuckGoImages as ddg
import os
import re
import shutil
import threading
import time
from pathlib import Path

print('Current directory: {}'.format(Path.cwd()))
def getCurrentDir():
  return Path.cwd()

screenshot_folder = getCurrentDir() / Path('sega saturn') / Path('screenshots')
def getScreenshotFolder():
  global screenshot_folder
  return screenshot_folder

games_folder = getCurrentDir() / Path('sega saturn')
def getGamesFolder():
  global games_folder
  return games_folder

temp_folder = getCurrentDir() / Path('temp')
def getTempFolder():
  global temp_folder
  return temp_folder

def getImagesTempFolder():
  return getTempFolder() / Path('images')

def getScreenshotsTempFolder():
  return getTempFolder() / Path('screenshots')

def cleanName(name):
  return re.sub('\s*\(.*\)\s*', '', name)

def get_game_list():
  sd_directory = getGamesFolder()
  game_list = []
  extensions = ['ccd', 'img', 'cue', 'iso']
  for extension in extensions:
    for filename in sd_directory.glob('**/*.{}'.format(extension)):
      directory = filename.parent
      dirname = directory.name
      if 'System Volume Information' in dirname:
        continue

      if directory.is_dir() and dirname not in game_list:
        game_list.append(dirname)

  return game_list

def get_thumbnail(game_name):
  output_dir = getScreenshotsTempFolder()
  image_file = output_dir / Path('{}.jpg'.format(game_name))
  if image_file.exists():
    return image_file

def _download_thumbnails(search_query, max_thumbnails=12):
  temp_directory = getImagesTempFolder()
  if temp_directory.exists():
    shutil.rmtree(temp_directory)

  ddg.download(search_query,
               max_urls=max_thumbnails,
               folder=temp_directory,
               thumbnails=True,
               target_resolution=(256,192))

  return True

class AsyncJob:
  def __init__(self, func):
    self.thread = threading.Thread(target=self.wrapFunc, args=(func,))
    self.exception = None
    self.return_code = 0
    self.thread.start()

  def wrapFunc(self, func):
    try:
      self.return_code = func()
      if not self.return_code:
        self.return_code = True
    except Exception as e:
      self.exception = e

  def done(self):
    if self.thread.is_alive():
      self.thread.join(0.1)

    if self.thread.is_alive():
      return False
    else:
      if self.exception:
        raise self.exception
      else:
        return self.return_code

