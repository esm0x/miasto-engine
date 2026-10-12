"""Minimal UI driver over adb + uiautomator: tap by visible text, type, screenshot.

    python ui.py SERIAL tap "Wybierz adres"
    python ui.py SERIAL tapfirst "Dom jednorodzinny|Boguszowice"   (regex, first match)
    python ui.py SERIAL type 12
    python ui.py SERIAL texts                                       (visible texts)
    python ui.py SERIAL shot out.png
"""
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ADB = r"C:\Users\Marcin\AppData\Local\Android\Sdk\platform-tools\adb.exe"


def adb(serial, *args, binary=False):
    out = subprocess.run([ADB, "-s", serial, *args], capture_output=True)
    return out.stdout if binary else out.stdout.decode("utf-8", "replace")


def nodes(serial):
    for _ in range(3):
        adb(serial, "shell", "uiautomator", "dump", "/sdcard/ui.xml")
        xml = adb(serial, "shell", "cat", "/sdcard/ui.xml")
        if "<hierarchy" in xml:
            root = ET.fromstring(xml[xml.index("<hierarchy"):])
            return list(root.iter("node"))
        time.sleep(1)
    raise SystemExit("no ui dump")


def center(node):
    x1, y1, x2, y2 = map(int, re.findall(r"\d+", node.get("bounds")))
    return (x1 + x2) // 2, (y1 + y2) // 2


def find(serial, pattern):
    rx = re.compile(pattern)
    for n in nodes(serial):
        label = n.get("text") or n.get("content-desc") or ""
        if label and rx.search(label):
            return n
    return None


def main():
    serial, cmd, *rest = sys.argv[1:]
    if cmd in ("tap", "tapfirst"):
        n = find(serial, rest[0] if cmd == "tapfirst" else "^" + re.escape(rest[0]) + "$")
        if n is None:
            raise SystemExit(f"not found: {rest[0]}")
        x, y = center(n)
        adb(serial, "shell", "input", "tap", str(x), str(y))
        print(f"tapped {n.get('text') or n.get('content-desc')!r} at {x},{y}")
        time.sleep(float(rest[1]) if len(rest) > 1 else 1.5)
    elif cmd == "type":
        adb(serial, "shell", "input", "text", rest[0].replace(" ", "%s"))
        time.sleep(0.8)
    elif cmd == "texts":
        seen = []
        for n in nodes(serial):
            t = n.get("text") or n.get("content-desc")
            if t and t not in seen:
                seen.append(t)
        print(" | ".join(seen))
    elif cmd == "shot":
        png = adb(serial, "exec-out", "screencap", "-p", binary=True)
        if png[1:4] != b"PNG":
            raise SystemExit(f"empty screencap, {rest[0]} not written")
        open(rest[0], "wb").write(png)
        print("shot", rest[0])


if __name__ == "__main__":
    main()
