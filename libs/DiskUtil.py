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

temp_Folder = getCurrentDir() / Path('temp')
def getTempFolder():
  global temp_Folder
  return temp_Folder

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
  output_dir = getScreenshotFolder()
  image_file = output_dir / Path('{}.jpg'.format(game_name))
  if image_file.exists():
    return image_file

def _download_thumbnails(search_query, max_thumbnails=12):
  temp_directory = getTempFolder()
  if temp_directory.exists():
    shutil.rmtree(temp_directory)

  ddg.download(search_query,
               max_urls=max_thumbnails,
               folder=temp_directory,
               thumbnails=True,
               target_resolution=(256,192))

class QueryResults:
  def __init__(self, search_query, max_thumbnails):
    self.thread = threading.Thread(target=_download_thumbnails,
                                   args=(search_query, max_thumbnails))
    self.thread.start()

  def done(self):
    self.thread.join(0.1)
    return not self.thread.is_alive()
