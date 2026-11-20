"""Board, CircuitPython and storage information. Nothing is driven."""

import os

import board
import microcontroller

from bringup._board import banner

banner("info")
u = os.uname()
print("CircuitPython:", u.version)
print("machine:", u.machine)
print("board_id:", board.board_id)
print("cpu frequency: %d Hz" % microcontroller.cpu.frequency)
print("cpu uid:", "".join("%02x" % b for b in microcontroller.cpu.uid))
print("nvm bytes:", len(microcontroller.nvm) if microcontroller.nvm is not None else None)
st = os.statvfs("/")
block = st[0]
total = st[2] * block
free = st[3] * block
print("CIRCUITPY: total %d bytes, free %d bytes, used %d bytes" % (total, free, total - free))


def walk(path, depth=0):
    size = 0
    for name in sorted(os.listdir(path)):
        full = path.rstrip("/") + "/" + name
        mode = os.stat(full)[0]
        if mode & 0x4000:
            sub = walk(full, depth + 1)
            print("  " * depth + "%-28s %8d (dir)" % (name + "/", sub))
            size += sub
        else:
            n = os.stat(full)[6]
            if depth < 1:
                print("  " * depth + "%-28s %8d" % (name, n))
            size += n
    return size


walk("/")
print("Expected: about 1 MiB total on the 2 MB W25Q16JV board (Pico build).")
