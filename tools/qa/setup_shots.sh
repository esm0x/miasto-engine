#!/usr/bin/env bash
# Usage: setup_shots.sh SERIAL [night]  - installs the Żory debug APK and prepares it for store screenshots.
# Example made for Żory (12.10.2026): paths, package, address and stop are that city's. Copy and adapt.
set -u
export MSYS_NO_PATHCONV=1 PYTHONIOENCODING=utf-8
S=$1
A=/c/Users/Marcin/AppData/Local/Android/Sdk/platform-tools/adb.exe
P=com.adminstack.zory
HERE=$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")
ui() { python "$HERE/ui.py" "$S" "$@"; }

$A -s $S install -r "C:/Users/Marcin/Documents/APKA/files/miasto-engine/app/build/outputs/apk/zory/debug/app-zory-debug.apk" | tail -1
$A -s $S shell pm grant $P android.permission.POST_NOTIFICATIONS
$A -s $S shell cmd alarm set-timezone Pacific/Kiritimati
$A -s $S shell cmd uimode night "${2:-no}"
$A -s $S shell settings put global sysui_demo_allowed 1
demo() { $A -s $S shell am broadcast -f 0x10000000 -a com.android.systemui.demo -e command "$@" >/dev/null; }
demo enter
demo battery -e level 100 -e plugged false
demo network -e wifi show -e level 4 -e mobile show -e datatype none -e level 4
demo notifications -e visible false

$A -s $S shell am start -n $P/com.adminstack.miasto.MainActivity >/dev/null; sleep 10
ui tap "Śmieci" 2; ui tap "Wybierz adres" 2; ui tap "Dom jednorodzinny" 2
ui tap "Szukaj ulicy" 1; ui type Wodzis; ui tap "Wodzisławska" 2
ui tap "np. 38 albo 128B" 1; ui type 218; ui tap "Zapisz adres" 3
ui tap "Transport" 15
ui tap "Szukaj przystanku" 1; ui type Centrum; ui tapfirst "^Centrum Przesiadkowe$" 3
ui tap "Ulubiony przystanek" 2
ui tap "Start" 3
