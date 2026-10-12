#!/usr/bin/env bash
# Usage: shots.sh SERIAL OUTDIR [set]   set = phone (all 8) | tablet (4)
# Example made for Żory (12.10.2026): paths, package, address and stop are that city's. Copy and adapt.
set -u
export MSYS_NO_PATHCONV=1 PYTHONIOENCODING=utf-8
S=$1; R=$2; SET=${3:-phone}
A=/c/Users/Marcin/AppData/Local/Android/Sdk/platform-tools/adb.exe
P=com.adminstack.zory
HERE=$(cygpath -m "$(cd "$(dirname "$0")" && pwd)")
ui() { python "$HERE/ui.py" "$S" "$@"; }
clock() { T=$($A -s $S shell date +%H%M | tr -d '\r'); $A -s $S shell am broadcast -f 0x10000000 -a com.android.systemui.demo -e command clock -e hhmm $T >/dev/null; }
back() { $A -s $S shell input keyevent KEYCODE_BACK; sleep 1; }

$A -s $S shell cmd alarm set-timezone America/New_York
$A -s $S shell cmd uimode night no
$A -s $S shell am force-stop $P; sleep 1
$A -s $S shell am start -n $P/com.adminstack.miasto.MainActivity >/dev/null; sleep 10
$A -s $S shell date

if [ "$SET" = phone ]; then
  clock; ui tap "Start" 3; ui shot $R/01-start.png
  ui tap "Śmieci" 3; clock; ui shot $R/02-odpady.png
  ui tap "Więcej" 2; ui tap "Co dziś otwarte" 4; clock; ui shot $R/03-co-otwarte.png; back
  ui tap "Transport" 4; clock; ui shot $R/04-autobusy.png
  ui tap "Wydarzenia" 3; clock; ui shot $R/05-wydarzenia.png
  ui tap "Więcej" 2; ui tap "Wiadomości" 5; clock; ui shot $R/06-wiadomosci.png; back
  ui tap "Gdzie wyrzucić" 3; ui tap "Czego szukasz?" 1; ui type "styropian"; back; clock; ui shot $R/07-gdzie-wyrzucic.png; back
  $A -s $S shell cmd uimode night yes; sleep 3; ui tap "Start" 4; clock; ui shot $R/08-ciemny-motyw.png
  $A -s $S shell cmd uimode night no
else
  clock; ui tap "Start" 3; ui shot $R/01-start.png
  ui tap "Więcej" 2; ui tap "Co dziś otwarte" 4; clock; ui shot $R/02-co-otwarte.png; back
  ui tap "Śmieci" 3; ui tap "Kalendarz" 3; clock; ui shot $R/03-kalendarz-odpadow.png; ui tap "Lista" 2
  ui tap "Wydarzenia" 3; clock; ui shot $R/04-wydarzenia.png
fi
