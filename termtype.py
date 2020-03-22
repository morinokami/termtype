import curses
import dataclasses
import random
import time
from typing import List
from typing import Tuple
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _curses import _CursesWindow

    Window = _CursesWindow
else:
    from typing import Any

    Window = Any

RESULT_ROW = 0
INPUT_ROW = 1
TEST_LENGTH = 20


@dataclasses.dataclass
class Result:
    count: int = 0
    correct_words: List[str] = None
    duration: float = 0

    def update(self, word: str, input: str, duration: float) -> None:
        self.count += 1
        if word == input:
            if self.correct_words is None:
                self.correct_words = []
            self.correct_words.append(word)
        self.duration += duration

    def get(self) -> Tuple[float, float, float]:
        if self.count == 0:
            return 0, 0, 0

        cpm = (len("".join(self.correct_words)) / self.duration) * 60
        wpm = (len(self.correct_words) / self.duration) * 60
        accuracy = len(self.correct_words) / self.count

        return cpm, wpm, accuracy


class TypingSpeedTest:
    def __init__(self):
        with open("./words.txt") as f:
            self.words = f.read().split("\n")
            random.shuffle(self.words)
        self.result = Result()

    def get_input(self, word: str, timeout: float, stdscr: Window) -> str:
        stdscr.addstr(INPUT_ROW, 0, f"{word} > ")
        stdscr.refresh()

        result = ""
        ch = 0
        while ch not in (curses.KEY_ENTER, 10, 13):
            start = time.time()
            curses.halfdelay(int(timeout * 10))
            ch = stdscr.getch()
            if ch in (curses.KEY_BACKSPACE, 8, 127):
                result = result[:-1]
                stdscr.delch(INPUT_ROW, len(f"{word} > ") + len(result))
            else:
                result += chr(ch)
                stdscr.addch(
                    INPUT_ROW, len(f"{word} > ") + len(result) - 1, ch
                )
            stdscr.refresh()
            elapsed = time.time() - start
            timeout -= elapsed

        return result[:-1]

    def continue_test(self) -> bool:
        return self.result.duration < TEST_LENGTH

    def test(self, stdscr) -> None:
        start = time.time()
        word = self.words.pop()
        input = self.get_input(
            word, TEST_LENGTH - self.result.duration, stdscr
        )
        duration = time.time() - start
        self.result.update(word, input, duration)

    def show_result(self, stdscr: Window) -> None:
        cpm, wpm, accuracy = self.result.get()

        stdscr.addstr(
            RESULT_ROW,
            0,
            f"cpm: {cpm:03.1f}, wpm: {wpm:.1f}, accuracy: {accuracy:.1%}",
        )

    def main(self, stdscr: Window) -> None:
        while self.continue_test():
            stdscr.clear()
            self.show_result(stdscr)
            try:
                self.test(stdscr)
            except ValueError:
                curses.nocbreak()
                stdscr.clear()
                self.show_result(stdscr)
                stdscr.addstr(INPUT_ROW, 0, "finished")
                stdscr.getkey()
                return


if __name__ == "__main__":
    test = TypingSpeedTest()
    curses.wrapper(test.main)
