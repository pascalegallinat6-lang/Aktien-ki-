import yfinance as yf
import pandas as pd
import numpy as np
import time

# ============================================================
# AKTIEN KI SCANNER V4
# Swing-Trading / Volatilität / Momentum
#
# Hinweis:
# Die Signale sind technische Analyse und keine Garantie
# für Gewinne.
# ============================================================

AKTIEN = [
    "NVDA", "TSLA", "AMD", "MSTR", "COIN",
    "PLTR", "NFLX", "META", "AMZN", "GOOGL",
    "AAPL", "MSFT", "AVGO", "MU", "SMCI",
    "JPM", "BAC", "XOM", "CVX", "CAT",
    "BA", "UBER", "SHOP", "ORCL", "CRM",
    "ADBE", "QCOM", "INTC", "ARM", "HOOD"
]

# ============================================================
# WKN / ISIN
#
# Nur Zuordnungen verwenden, die zum konkreten Wertpapier
# passen. Nicht hinterlegte Werte werden nicht geraten.
# ============================================================

WERTPAPIERE = {
    "NVDA": {
        "wkn": "918422",
        "isin": "US67066G1040"
    },
    "TSLA": {
        "wkn": "A1CX3T",
        "isin": "US88160R1014"
    },
    "AMD": {
        "wkn": "863186",
        "isin": "US0079031078"
    },
    "MSTR": {
        "wkn": "A0J3ER",
        "isin": "US5949724083"
    },
    "AAPL": {
        "wkn": "865985",
        "isin": "US0378331005"
    },
    "MSFT": {
        "wkn": "870747",
        "isin": "US5949181045"
    },
    "AMZN": {
        "wkn": "906866",
        "isin": "US0231351067"
    },
    "GOOGL": {
        "wkn": "A14Y6F",
        "isin": "US02079K3059"
    },
    "META": {
        "wkn": "A1JWVX",
        "isin": "US30303M1027"
    },
    "JPM": {
        "wkn": "850628",
        "isin": "US46647P1049"
    },
    "CRM": {
        "wkn": "A3DB79",
        "isin": "CA79467F1062"
    }
}


def hole_daten(symbol):

    try:

        aktie = yf.Ticker(symbol)

        df = aktie.history(
            period="6mo",
            interval="1d",
            auto_adjust=True
        )

        if df.empty or len(df) < 70:
            return None

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        kurs = float(close.iloc[-1])

        # ====================================================
        # DURCHSCHNITTE
        # ====================================================

        sma20 = float(
            close.rolling(20).mean().iloc[-1]
        )

        sma50 = float(
            close.rolling(50).mean().iloc[-1]
        )

        # ====================================================
        # ATR 14
        # ====================================================

        vorheriger_close = close.shift(1)

        true_range = pd.concat(
            [
                high - low,
                (high - vorheriger_close).abs(),
                (low - vorheriger_close).abs()
            ],
            axis=1
        ).max(axis=1)

        atr = float(
            true_range.rolling(14).mean().iloc[-1]
        )

        atr_prozent = (
            atr / kurs * 100
        )

        # ====================================================
        # MOMENTUM
        # ====================================================

        momentum5 = (
            kurs / float(close.iloc[-6]) - 1
        ) * 100

        momentum20 = (
            kurs / float(close.iloc[-21]) - 1
        ) * 100

        momentum60 = (
            kurs / float(close.iloc[-61]) - 1
        ) * 100

        # ====================================================
        # VOLATILITÄT
        # ====================================================

        renditen = close.pct_change().dropna()

        volatilitaet20 = (
            renditen.tail(20).std()
            * np.sqrt(252)
            * 100
        )

        # ====================================================
        # HOCH / TIEF
        # ====================================================

        hoch20 = float(
            high.tail(20).max()
        )

        tief20 = float(
            low.tail(20).min()
        )

        abstand_hoch = (
            (hoch20 - kurs) / kurs * 100
        )

        # ====================================================
        # VOLUMEN
        # ====================================================

        durchschnitt_volumen = float(
            volume.tail(20).mean()
        )

        aktuelles_volumen = float(
            volume.iloc[-1]
        )

        volumen_faktor = (
            aktuelles_volumen
            / durchschnitt_volumen
            if durchschnitt_volumen > 0
            else 0
        )

        # ====================================================
        # TREND
        # ====================================================

        aufwaertstrend = (
            kurs > sma20
            and sma20 > sma50
        )

        abwaertstrend = (
            kurs < sma20
            and sma20 < sma50
        )

        # ====================================================
        # LONG SCORE
        # ====================================================

        long_score = 0
        long_gruende = []

        if aufwaertstrend:
            long_score += 25
            long_gruende.append(
                "Aufwärtstrend über SMA20/SMA50"
            )

        if momentum20 >= 15:
            long_score += 25
            long_gruende.append(
                "starkes Momentum"
            )
        elif momentum20 >= 5:
            long_score += 15
            long_gruende.append(
                "positives Momentum"
            )

        if volumen_faktor >= 1.5:
            long_score += 20
            long_gruende.append(
                "stark erhöhtes Volumen"
            )
        elif volumen_faktor >= 1.1:
            long_score += 10
            long_gruende.append(
                "überdurchschnittliches Volumen"
            )

        if atr_prozent >= 3:
            long_score += 15
            long_gruende.append(
                "hohe Schwankungsbreite"
            )
        elif atr_prozent >= 2:
            long_score += 8

        # ====================================================
        # ABWÄRTS SCORE
        # ====================================================

        short_score = 0
        short_gruende = []

        if abwaertstrend:
            short_score += 25
            short_gruende.append(
                "Abwärtstrend unter SMA20/SMA50"
            )

        if momentum20 <= -15:
            short_score += 25
            short_gruende.append(
                "stark negatives Momentum"
            )
        elif momentum20 <= -5:
            short_score += 15
            short_gruende.append(
                "negatives Momentum"
            )

        if volumen_faktor >= 1.5:
            short_score += 20
            short_gruende.append(
                "stark erhöhtes Volumen"
            )

        if atr_prozent >= 3:
            short_score += 15
            short_gruende.append(
                "hohe Schwankungsbreite"
            )

        # ====================================================
        # TAKE-PROFIT SCORE
        # ====================================================

        tp_score = 0
        tp_gruende = []

        if aufwaertstrend:
            tp_score += 20
            tp_gruende.append(
                "Aufwärtstrend"
            )

        if momentum20 >= 15:
            tp_score += 25
            tp_gruende.append(
                "starke Kursbewegung"
            )

        if abstand_hoch <= 3:
            tp_score += 30
            tp_gruende.append(
                "sehr nahe am 20-Tage-Hoch"
            )
        elif abstand_hoch <= 5:
            tp_score += 20
            tp_gruende.append(
                "nahe am 20-Tage-Hoch"
            )

        if volatilitaet20 >= 40:
            tp_score += 15
            tp_gruende.append(
                "hohe kurzfristige Volatilität"
            )

        if volumen_faktor >= 1.5:
            tp_score += 10
            tp_gruende.append(
                "erhöhtes Volumen"
            )

        tp_score = min(tp_score, 100)

        # ====================================================
        # SIGNAL
        # ====================================================

        if tp_score >= 70:

            signal = "🟡 TAKE-PROFIT-KANDIDAT"
            score = tp_score
            gruende = tp_gruende

        elif long_score >= 65:

            signal = "🟢 LONG-KANDIDAT"
            score = long_score
            gruende = long_gruende

        elif short_score >= 65:

            signal = "🔴 ABWÄRTS-KANDIDAT"
            score = short_score
            gruende = short_gruende

        else:

            signal = "⚪ BEOBACHTEN"
            score = max(
                long_score,
                short_score,
                tp_score
            )
            gruende = []

        # ====================================================
        # SWING-ZONEN
        # ====================================================
        #
        # Diese Werte sind technische Orientierungen.
        # Keine garantierten Ziele.
        #

        if signal == "🟢 LONG-KANDIDAT":

            einstieg_unten = kurs - atr * 0.50
            einstieg_oben = kurs + atr * 0.10

            stop_loss = (
                einstieg_unten - atr * 0.75
            )

            take_profit1 = (
                kurs + atr * 1.0
            )

            take_profit2 = (
                kurs + atr * 2.0
            )

        elif signal == "🔴 ABWÄRTS-KANDIDAT":

            einstieg_unten = kurs - atr * 0.10
            einstieg_oben = kurs + atr * 0.50

            stop_loss = (
                einstieg_oben + atr * 0.75
            )

            take_profit1 = (
                kurs - atr * 1.0
            )

            take_profit2 = (
                kurs - atr * 2.0
            )

        else:

            einstieg_unten = kurs - atr * 0.50
            einstieg_oben = kurs + atr * 0.50

            stop_loss = kurs - atr

            take_profit1 = kurs + atr

            take_profit2 = kurs + atr * 2

        # ====================================================
        # WKN / ISIN
        # ====================================================

        wertpapier = WERTPAPIERE.get(
            symbol,
            {}
        )

        wkn = wertpapier.get(
            "wkn",
            "nicht hinterlegt"
        )

        isin = wertpapier.get(
            "isin",
            "nicht hinterlegt"
        )

        return {

            "symbol": symbol,
            "wkn": wkn,
            "isin": isin,

            "kurs": kurs,

            "score": score,
            "signal": signal,

            "atr": atr,
            "atr_prozent": atr_prozent,

            "volatilitaet20":
                volatilitaet20,

            "momentum5":
                momentum5,

            "momentum20":
                momentum20,

            "momentum60":
                momentum60,

            "abstand_hoch":
                abstand_hoch,

            "volumen_faktor":
                volumen_faktor,

            "einstieg_unten":
                einstieg_unten,

            "einstieg_oben":
                einstieg_oben,

            "stop_loss":
                stop_loss,

            "take_profit1":
                take_profit1,

            "take_profit2":
                take_profit2,

            "gruende":
                gruende
        }

    except Exception as e:

        print(
            f"Fehler bei {symbol}: {e}"
        )

        return None


def scanner():

    print()
    print("=" * 75)
    print("             AKTIEN KI SCANNER V4")
    print("          SWING / VOLATILITÄT / SIGNAL")
    print("=" * 75)
    print()

    ergebnisse = []

    for symbol in AKTIEN:

        print(
            f"Analysiere {symbol} ..."
        )

        daten = hole_daten(symbol)

        if daten:
            ergebnisse.append(daten)

        time.sleep(0.5)

    # Nach Score sortieren
    ergebnisse.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    print()
    print("=" * 75)
    print("                    TOP SIGNALS")
    print("=" * 75)

    for platz, daten in enumerate(
        ergebnisse,
        start=1
    ):

        print()
        print(
            f"#{platz} 📊 {daten['symbol']}"
        )

        print(
            f"WKN:               "
            f"{daten['wkn']}"
        )

        print(
            f"ISIN:              "
            f"{daten['isin']}"
        )

        print(
            f"Kurs:              "
            f"${daten['kurs']:.2f}"
        )

        print(
            f"Signal:            "
            f"{daten['signal']}"
        )

        print(
            f"Score:             "
            f"{daten['score']}/100"
        )

        print(
            f"ATR:               "
            f"${daten['atr']:.2f}"
        )

        print(
            f"ATR %:             "
            f"{daten['atr_prozent']:.2f}%"
        )

        print(
            f"Volatilität 20T:   "
            f"{daten['volatilitaet20']:.2f}%"
        )

        print(
            f"Momentum 5T:       "
            f"{daten['momentum5']:.2f}%"
        )

        print(
            f"Momentum 20T:      "
            f"{daten['momentum20']:.2f}%"
        )

        print(
            f"Momentum 60T:      "
            f"{daten['momentum60']:.2f}%"
        )

        print(
            f"Volumen Faktor:    "
            f"{daten['volumen_faktor']:.2f}x"
        )

        print(
            f"Abstand Hoch:      "
            f"{daten['abstand_hoch']:.2f}%"
        )

        print()
        print("TECHNISCHE ZONEN")

        print(
            f"Einstiegszone:     "
            f"${daten['einstieg_unten']:.2f}"
            f" - "
            f"${daten['einstieg_oben']:.2f}"
        )

        print(
            f"Stop-Loss-Zone:    "
            f"${daten['stop_loss']:.2f}"
        )

        print(
            f"Take Profit 1:     "
            f"${daten['take_profit1']:.2f}"
        )

        print(
            f"Take Profit 2:     "
            f"${daten['take_profit2']:.2f}"
        )

        if daten["gruende"]:

            print()
            print("Gründe:")

            for grund in daten["gruende"]:

                print(
                    f"  • {grund}"
                )

    print()
    print("=" * 75)
    print("Scanner beendet.")
    print("=" * 75)
    print()
    print(
        "Hinweis: Einstiegs-, Stop- und "
        "Take-Profit-Werte sind technische "
        "Orientierungen und keine "
        "Handelsempfehlungen oder "
        "Gewinngarantien."
    )


if __name__ == "__main__":
    scanner()
