# 10: Miernik szczytowy mierzy realny sygnał (WASAPI loopback)

**What to build:** Miernik szczytowy w konsoli operatora pokazuje poziom
sygnału, który naprawdę leci do domyślnego urządzenia renderującego — osobno
L i R, w dBFS — zamiast wartości z symulatora. Źródło pomiaru: WASAPI loopback
przez `pyaudiowpatch`, tryb callbackowy (blokujący `read()` zawiesza się, gdy
nic nie jest renderowane). Miernik ma trzy stany: pomiar, cisza i **brak
pomiaru**; trzeci jest obowiązkowy i nie wolno go pokazywać jako ciszy.
Decyzja i uzasadnienie: `docs/adr/0006-miernik-realny-sygnal.md`.

**Blocked by:** None (can start immediately)

**Status:** ready-for-human

- [x] Przy pauzie i stopie miernik pokazuje `-∞ dBFS`, nie resztkę poprzedniego poziomu
- [x] Podczas grania poziom reaguje na suwak głośności i na fade (pomiar jest za nimi)
- [x] Zmiana domyślnego urządzenia wyjściowego przełącza pomiar bez restartu aplikacji
- [x] Wyjście w trybie exclusive, odłączone urządzenie albo błąd PortAudio → „brak pomiaru", nie cisza
- [x] Brak `pyaudiowpatch` w środowisku → aplikacja startuje, miernik w stanie „brak pomiaru"
- [x] W torze pomiaru nie ma `math.sin` ani `random` (symulator usunięty z `peak_meter.py`)
- [x] `pyinstaller main.spec` buduje exe zawierający `_portaudiowpatch.pyd`
- [x] `pyaudiowpatch` przypięty w `requirements.txt`

## Comments

Zakres świadomie ograniczony: cały mix systemowy (Q4), domyślne urządzenie bez
wyboru w ustawieniach (Q3), bez filtrowania po procesie. Filtrowanie po procesie
(Process Loopback, Win10 2004+) to osobny ticket, jeśli okaże się potrzebne.

Realizacja: pomiar siedzi w `playback/audio_meter.py` — wątek nadzorujący
otwiera loopback domyślnego urządzenia WASAPI w trybie callbackowym i zapisuje
ostatni `LevelSample` pod zamkiem. Co sekundę sprawdza `is_active()` strumienia
i indeks domyślnego urządzenia; zmiana urządzenia albo błąd PortAudio zamyka
strumień i od razu otwiera go ponownie, bez restartu aplikacji. Brak
`pyaudiowpatch` kończy wątek, a miernik zostaje w stanie „brak pomiaru”.
Reguły stanu są czyste w `playback/meter_policy.py`: brak świeżych danych
(< 250 ms) przy graniu to `NO_MEASUREMENT`, nigdy cisza.

Stan „brak pomiaru” przy braku `pyaudiowpatch` widać od pierwszej próby
odtwarzania, nie na starcie: zgodnie z tabelą ADR 0006 sesja, która nie gra,
pokazuje ciszę, a nie brak pomiaru.

`ui/peak_meter.py`: symulator (`AudioPeakProvider`, `math.sin`, `random`)
zniknął; został rysunek IEC i peak hold. `reset()` i `set_no_measurement()`
czyszczą słupki oraz peak hold natychmiast, więc pauza i stop pokazują
`-∞ dBFS` zamiast resztki poprzedniego pomiaru. Stan „brak pomiaru” rysuje
kratkę i etykietę z i18n. Przy okazji przywrócone polskie znaki w komentarzach
po commicie WIP.

`playback/session.py`: `is_audio_rendering()` odpowiada, czy bieżąca pozycja
naprawdę oddaje dźwięk — `is_playing` zostaje prawdziwe w pauzie, obraz i wideo
bez ścieżki dźwiękowej nie mają czego mierzyć, a fade out nadal gra, więc flaga
przejścia nie wyłącza pomiaru. `window.py` tylko spina: w stanie ciszy woła
`reset()`, w braku pomiaru `set_no_measurement()`, a w pomiarze przekazuje L/R
z `AudioMeter`.

Weryfikacja: `pytest` — 144 zielone (nowe testy callbacku i przełączania
urządzenia), `ruff check .` czysto. Pomiar na maszynie deweloperskiej: blok
0,5 FS stereo dał L/R `-6.02 dBFS`; po zatrzymaniu renderowania świeży blok
ciszy daje `SILENT`, a brak danych `NO_MEASUREMENT`. Smoke Qt: po sygnale
`-6 dB` `reset()` natychmiast zeruje słupki i emituje `-∞`; `Paused` daje
ciszę, wideo bez ścieżki dźwiękowej daje ciszę, a fade out nadal mierzy.
Build `pyinstaller main.spec` przechodzi,
a `dist/main/_internal/` zawiera `_portaudiowpatch.cp314-win_amd64.pyd`;
exe startuje.

Do potwierdzenia na sprzęcie: fizyczne odłączenie urządzenia i przełączenie
domyślnego wyjścia w trakcie grania (kod pokryty testami `_healthy`, ale
nie da się tego zastąpić testem) oraz końcówka w trybie exclusive.
