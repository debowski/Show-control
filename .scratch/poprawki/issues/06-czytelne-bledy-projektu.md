# 06: Czytelne błędy pliku projektu

**What to build:** Zepsuty lub niepełny plik projektu daje zrozumiały komunikat
(„nieprawidłowy plik projektu") ze wskazaniem, czego brakuje lub co jest
nie tak, zamiast surowego wyjątku w oknie. Błąd zapisu — np. brak uprawnień —
też mówi po ludzku. Operator nie traci przy tym dotychczasowej playlisty.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] Uszkodzony JSON daje komunikat po ludzku, nie surowy wyjątek
- [ ] Brak wymaganego pola lub zły typ daje wskazanie, które pole jest błędne
- [ ] Błąd zapisu (brak uprawnień, zajęty plik) daje czytelny komunikat
- [ ] Po nieudanym wczytaniu dotychczasowa playlista zostaje nietknięta
