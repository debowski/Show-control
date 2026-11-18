# ADR 0006 — Miernik szczytowy mierzy realny sygnał, nie symulację

**Status:** przyjęta
**Data:** 2026-11-18
**Kontekst:** `GLOSSARY.md` § Pomiar; `showcontrol/ui/peak_meter.py`;
`showcontrol/playback/audio_meter.py`; ticket 10; commit `3770ede`
(usunięcie analizatora widma)

## Kontekst

Miernik szczytowy w konsoli operatora rysuje od `v0.8.x` skalę IEC dBFS,
segmenty i peak hold — ale dane wejściowe są wymyślone. `AudioPeakProvider`
(`ui/peak_meter.py:234`) deklarował w docstringu „WASAPI z fallbackiem
estymacji dynamiki IEC", po czym liczył poziomy z `math.sin`, `random.uniform`
i głośności suwaka. Prawdziwe były tylko animacje: atak, tempo opadania
i czas peak holdu.

To nie jest brak funkcji ani niedokończony mockup. To przyrząd pomiarowy
z etykietą pomiarową, który podczas wydarzenia mówi operatorowi „-6 dB",
gdy nie zmierzył niczego. Analizator widma (`ui/spectrum_analyzer.py`) miał
ten sam defekt, ale nie miał żadnego konsumenta — usunięty w `3770ede`
wraz z kluczami i18n.

Pytanie brzmiało: da się zmierzyć sygnał, który naprawdę leci do publiczności,
nie odbierając przy tym dźwięku aplikacji?

## Decyzja

### Źródło pomiaru

Jedynym źródłem prawdy jest **WASAPI loopback domyślnego urządzenia
renderującego**, czytany przez `pyaudiowpatch`. Miernik pokazuje sygnał
**kierowany do urządzenia wyjściowego** — czyli po głośności aplikacji,
po fade i po głośności końcówki. Nie mierzy pliku, nie mierzy VLC, nie
mierzy „zamierzonego" poziomu.

### Brak pomiaru jest osobnym stanem

Miernik ma trzy stany, nie dwa:

| Stan | Kiedy | Co widać |
|---|---|---|
| pomiar | sesja gra i są świeże dane (< 250 ms) | słupki, etykieta `-x.x dB` |
| cisza | sesja nie gra, albo zmierzony poziom ≤ -60 dBFS | słupki zgaszone, `-∞ dBFS` |
| brak pomiaru | sesja gra, a danych nie ma lub są starsze niż 250 ms | słupki przygaszone, etykieta „brak pomiaru" |

Trzeci stan jest obowiązkowy. Loopback nie dostarcza danych, gdy nic nie jest
renderowane, więc „brak danych przy graniu" znaczy, że pomiar nie działa —
urządzenie się rozjechało, końcówka jest w trybie exclusive, strumień padł.
Pokazanie wtedy ciszy byłoby tym samym kłamstwem co symulacja, tylko w drugą
stronę.

### Urządzenie

Zawsze domyślne urządzenie renderujące, z automatycznym przełączeniem, gdy
system zmieni domyślne. Wybór urządzenia w ustawieniach nie wchodzi: aplikacja
gra na domyślne, a rozjazd domyślnego z tym, co słyszy publiczność, jest
widoczny jako „brak pomiaru", nie jako cicha konfiguracja.

### Zakres sygnału

Loopback łapie **cały mix systemowy** — także inne aplikacje. Przyjęte
świadomie: na wydarzeniu konsola gra sama, a filtrowanie po procesie wymaga
Process Loopback (Win10 2004+) przez własne `ctypes` na WASAPI, czego
`pyaudiowpatch` nie wystawia.

## Dlaczego nie inne drogi

| Droga | Dlaczego odpada |
|---|---|
| `libvlc_audio_set_callbacks` (`amem`) | Wymusza `aout=amem,none` — **aplikacja przestaje grać**. Docstring `vlc.py:2643`: „LibVLC will not output audio in any way". Dodatkowo tylko S16, ignoruje `audio_set_format`, gubi pacing na plikach audio-only (1,32×) |
| natywne API poziomów/widma | Nie istnieje w libVLC 3.x. `--visual=vuMeter` rysuje na wyjściu wideo i nic nie zwraca |
| `--sout` z `duplicate` | Tap przed aout i przed głośnością — fade byłby niewidoczny; drugi dekoder po stronie Pythona |
| equalizer (`libvlc_audio_equalizer_*`) | Zwraca **ustawienia**, nie pomiar sygnału |
| `audiobargraph_a` | Liczy tylko dodatnią połówkę (`if (ch > i_value[j])`, bez `fabs`), a wynik ląduje w zmiennej, do której `var_GetString` nie jest eksportowane z `libvlc.dll` |
| `amem` + własne wyjście do karty | Daje i dźwięk, i próbki, ale to reimplementacja aout: blokowanie w callbacku, latencja, dryf, brak `time_get`. Miernik wyprzedzałby publiczność |
| Wskaźnik „zamierzony poziom" (głośność × stan) | Nie kłamie, ale nic nie mierzy — dekoracja przebrana za przyrząd |

## Fakty zweryfikowane na maszynie deweloperskiej

2026-11-18, VLC 3.0.23, `pyaudiowpatch 0.2.12.9` (wheel cp314, 101 kB +
`_portaudiowpatch.pyd` 196 kB), Python 3.14, domyślne urządzenie
`M2752D (NVIDIA HDMI) [Loopback]`, 48 kHz, 2 kanały.

- 1024 próbki / kanał → ~47 callbacków/s.
- Cisza (nic nie renderowane) → **zero callbacków**, nie „blok zer" .
- Blokujący `stream.read()` przy braku renderowania **zawiesza się na stałe**
  — stąd tryb callbackowy.
- Liniowość: amplitudy 1,0 / 0,5 / 0,25 / 0,1 FS dały stałą deltę -38,0 dB
  względem oczekiwanej wartości. Skala jest poprawna; różnica to głośność
  końcówki, która w loopbacku jest uwzględniona.
- Koszt: `max()/min()` na `memoryview.cast('h')` ≈ 0,24 % rdzenia —
  `numpy` niepotrzebny.

## Konsekwencje

**Pozytywne**

- Miernik przestaje kłamać. Operator widzi sygnał, który naprawdę idzie na PA,
  z głośnością końcówki włącznie — czyli to, co słyszy publiczność.
- Fade i suwak głośności są widoczne na mierniku, bo mierzymy za nimi.
- „Brak pomiaru" daje operatorowi sygnał, że problem jest w torze pomiarowym,
  a nie w materiale.
- Znika 90 linii symulacji (`AudioPeakProvider`) i cała klasa widma.

**Negatywne**

- **Nowa zależność natywna** w exe: `pyaudiowpatch` + `_portaudiowpatch.pyd`.
  Wchodzi do `requirements.txt` i `main.spec`; bramą odbioru staje się build
  `pyinstaller main.spec` z DLL-ką w środku.
- Loopback łapie cały mix systemowy (świadomie, patrz wyżej).
- Tryb exclusive na końcówce, zmiana urządzenia i błąd PortAudio to realne
  ścieżki awarii — dlatego stan „brak pomiaru" nie jest opcją.
- Pomiar jest post-głośność-końcówki: przy cichym urządzeniu miernik pokaże
  niski poziom, mimo poprawnie zmasterowanego pliku. To zamierzone.

## Odrzucone alternatywy

**Zostawić symulację i dodać etykietę „symulacja"** — przyrząd, o którym
operator musi pamiętać, że nie mierzy, jest gorszy od braku przyrządu.

**Usunąć miernik z UI** — uczciwe i najtańsze, ale odbiera operatorowi jedyne
narzędzie do sprawdzenia, czy sygnał w ogóle wychodzi. Wybrano pomiar.

**Mierzyć przez `amem` i odtwarzać dźwięk samemu** — pełna kontrola nad
próbkami za cenę reimplementacji wyjścia audio i nowych klas błędów
(latencja, dryf, blokowanie dekodera) w aplikacji, która ma po prostu grać.

**Filtrować loopback po procesie** — Process Loopback nie jest wystawiony
przez `pyaudiowpatch`; własne `ctypes` na WASAPI to materiał na osobny ticket.
