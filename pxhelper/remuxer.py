import os
import sys
import codecs
import zipfile
import subprocess

from . import config


class UgoiraRemuxer():
    def __init__(self, zippath, frames, resolution):
        self.zippath = zippath
        self.frames = frames
        self.resolution = resolution
        self.workpath = os.path.dirname(os.path.abspath(zippath))

    def _generate_config_file(self, frames):
        with codecs.open(
                self.workpath + "/config.txt", mode="w",
                encoding="utf-8") as f:
            # https://trac.ffmpeg.org/wiki/Slideshow#Concatdemuxer
            for frame in frames:
                f.write("file 'imgs/{0}'".format(frame['file']))
                f.write("\n")
                f.write("duration {0}".format(frame['delay'] / 1000))
                f.write("\n")
            f.write("file 'imgs/{0}'".format(frames[-1]['file']))

    def _unzip(self, zippath):
        with open(zippath, mode="rb") as f:
            zipfile.ZipFile(f).extractall(path=self.workpath + "/imgs/")

    def remux(self):
        self._unzip(self.zippath)
        self._generate_config_file(self.frames)
        if sys.platform == "win32":
            ffmpeg = '"{}"'.format(
                os.path.dirname(os.path.abspath(__file__)) + "/ffmpeg.exe")
        else:
            ffmpeg = "ffmpeg"
        subprocess.Popen(
            ffmpeg +
            " -f concat -i {0} -framerate 30 -vsync -1 -s {1} {2}".format(
                self.workpath + "/config.txt", self.resolution,
                self.workpath + "/remux." + config.remux_ext),
            shell=True)
