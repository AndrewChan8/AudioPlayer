import sys
import signal
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QUrl, QTimer, QSocketNotifier
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


AUDIO_FILE = Path("/home/andrewsushi/Music/01. monet - H2O.mp3")

def ms_to_mmss(ms: int) -> str:
  s = max(0, ms) // 1000
  return f"{s // 60:02d}:{s % 60:02d}"


class Player:
  def __init__(self, audio_file: Path, app: QCoreApplication):
    self.app = app
    self.audio_file = audio_file

    self.audio_output = QAudioOutput()
    self.player = QMediaPlayer()
    self.player.setAudioOutput(self.audio_output)

    if not self.audio_file.exists():
      print(f"ERROR: file not found: {self.audio_file}")
      self.app.quit()
      return

    url = QUrl.fromLocalFile(str(self.audio_file))
    self.player.setSource(url)
    self.player.play()

    # timer for position display
    self.timer = QTimer()
    self.timer.setInterval(1000)
    self.timer.timeout.connect(self._on_tick)
    self.timer.start()

    # stdin notifier
    self.notifier = QSocketNotifier(sys.stdin.fileno(), QSocketNotifier.Read)
    self.notifier.activated.connect(self._on_stdin_ready)

    print("Controls: p = play/pause | s <sec> = seek | q = quit")

  def _on_tick(self):
    pos = self.player.position()
    dur = self.player.duration()
    status = f"{ms_to_mmss(pos)} / {ms_to_mmss(dur)}"
    print(f"\r{status:<20}", end="", flush=True)

  def _on_stdin_ready(self, _fd: int):
    line = sys.stdin.readline()
    if not line:
      self.app.quit()
      return

    line = line.strip()
    print()  # move off the time line

    if line == "p":
      self.toggle_play()
    elif line.startswith("s "):
      try:
        sec = float(line.split(maxsplit=1)[1])
        self.seek_seconds(sec)
      except ValueError:
        print("Bad seek. Use: s 30")
    elif line == "q":
      self.app.quit()
    else:
      print("Unknown command. Use: p | s <sec> | q")

  # public API
  def toggle_play(self):
    if self.player.playbackState() == QMediaPlayer.PlayingState:
      self.player.pause()
    else:
      self.player.play()

  def seek_seconds(self, sec: float):
    self.player.setPosition(int(sec * 1000))


def main():
  app = QCoreApplication(sys.argv)
  signal.signal(signal.SIGINT, signal.SIG_DFL)

  _player = Player(AUDIO_FILE, app)

  return app.exec()


if __name__ == "__main__":
  sys.exit(main())
