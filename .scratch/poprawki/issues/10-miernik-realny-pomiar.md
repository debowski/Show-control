# 10: Miernik szczytowy mierzy realny sygnał (WASAPI loopback)

**What to build:** Miernik szczytowy w konsoli operatora pokazuje poziom
sygnału, który naprawdę leci do domyślnego urządzenia renderującego — osobno
L i R, w dBFS — zamiast wartości z symulatora. Źródło pomiaru: WASAPI loopback
przez `pyaudiowpatch`, tryb callbackowy (blokujący `read()` zawiesza się, gdy
nic nie jest renderowane). Miernik ma trzy stany: pomiar, cisza i **brak
pomiaru**; trzeci jest obowiązkowy i nie wolno go pokazywać jako ciszy.
Decyzja i uzasadnienie: `docs/adr/0006-miernik-realny-sygnal.md`.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Przy pauzie i stopie miernik pokazuje `-∞ dBFS`, nie resztkę poprzedniego poziomu
- [ ] Podczas grania poziom reaguje na suwak głośności i na fade (pomiar jest za nimi)
- [ ] Zmiana domyślnego urządzenia wyjściowego przełącza pomiar bez restartu aplikacji
- [ ] Wyjście w trybie exclusive, odłączone urządzenie albo błąd PortAudio → „brak pomiaru", nie cisza
- [ ] Brak `pyaudiowpatch` w środowisku → aplikacja startuje, miernik w stanie „brak pomiaru"
- [ ] W torze pomiaru nie ma `math.sin` ani `random` (symulator usunięty z `peak_meter.py`)
- [ ] `pyinstaller main.spec` buduje exe zawierający `_portaudiowpatch.pyd`
- [ ] `pyaudiowpatch` przypięty w `requirements.txt`

## Comments

Zakres świadomie ograniczony: cały mix systemowy (Q4), domyślne urządzenie bez
wyboru w ustawieniach (Q3), bez filtrowania po procesie. Filtrowanie po procesie
(Process Loopback, Win10 2004+) to osobny ticket, jeśli okaże się potrzebne.
