// Szablon (WeiDU, COMPILE EVALUATE_BUFFER): odpowiedz w dialogu Hedrona Kerdosa przenoszaca druzyne do nowej lokacji.
// %dlg% - dialog, %stany% - stany z wyborem gracza, %obszar% i %x%.%y% - wejscie obszaru (pierwszy wpis entrance w ARE).
EXTEND_BOTTOM ~%dlg%~ %stany%
  IF ~~ THEN REPLY ~[TEST] Zabierz nas do lokacji %obszar%.~ DO ~ActionOverride(Player1,LeaveAreaLUAPanic("%obszar%","",[%x%.%y%],0))
ActionOverride(Player2,LeaveAreaLUAPanic("%obszar%","",[%x%.%y%],0))
ActionOverride(Player3,LeaveAreaLUAPanic("%obszar%","",[%x%.%y%],0))
ActionOverride(Player4,LeaveAreaLUAPanic("%obszar%","",[%x%.%y%],0))
ActionOverride(Player5,LeaveAreaLUAPanic("%obszar%","",[%x%.%y%],0))
ActionOverride(Player6,LeaveAreaLUAPanic("%obszar%","",[%x%.%y%],0))~ EXIT
END
