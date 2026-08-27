import yfinance as yf
import pandas as pd
import numpy as np
import time

# ============================================================
# AKTIEN KI SCANNER V3
# Ziel:
# Aktien mit starken Bewegungen finden und unterscheiden:
# LONG / TAKE-PROFIT / ABWÄRTS / BEOBACHTEN
# ============================================================

AKTIEN = [
    "NVDA", "TSLA", "AMD", "MSTR", "COIN",
    "PLTR", "NFLX", "META", "AMZN", "GOOGL",
    "AAPL", "MSFT", "AVGO", "MU", "SMCI",
    "JPM", "BAC", "XOM", "CVX", "CAT",
    "BA", "UBER", "SHOP", "ORCL", "CRM",
    "ADBE", "QCOM", "INTC", "ARM", "HOOD"
]


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
        # GLEITENDE DURCHSCHNITTE
        # ====================================================

        sma20 = float(close.rolling(20).mean().iloc[-1])
        sma50 = float(close.rolling(50).mean().iloc[-1])

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

        atr14 = float(
            true_range.rolling(14).mean().iloc[-1]
        )

        atr_prozent = (
            atr14 / kurs * 100
        )

        # ====================================================
        # MOMENTUM
        # ====================================================

        momentum5 = (
            (kurs / float(close.iloc[-6])) - 1
        ) * 100

        momentum20 = (
            (kurs / float(close.iloc[-21])) - 1
        ) * 100

        momentum60 = (
            (kurs / float(close.iloc[-61])) - 1
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
            (hoch20 - kurs)
            / kurs
            * 100
        )

        abstand_tief = (
            (kurs - tief20)
            / kurs
            * 100
        )

        # ====================================================
        # VOLUMEN
        # ====================================================

        volumen20 = float(
            volume.tail(20).mean()
        )

        volumen_aktuell = float(
            volume.iloc[-1]
        )

        volumen_faktor = (
            volumen_aktuell / volumen20
            if volumen20 > 0
            else 0
        )

        # ====================================================
        # TREND
        # ====================================================

        trend_aufwaerts = (
            kurs > sma20 and
            sma20 > sma50
        )

        trend_abwaerts = (
            kurs < sma20 and
            sma20 < sma50
        )

        # ====================================================
        # SCORE
        # ====================================================

        long_score = 0
        short_score = 0

        gruende_long = []
        gruende_short = []

        # ----------------------------------------------------
        # LONG
        # ----------------------------------------------------

        if trend_aufwaerts:
            long_score += 25
            gruende_long.append(
                "Aufwärtstrend über SMA20/SMA50"
            )

        if momentum20 >= 15:
            long_score += 25
            gruende_long.append(
                "starkes 20-Tage-Momentum"
            )

        elif momentum20 >= 5:
            long_score += 15
            gruende_long.append(
                "positives 20-Tage-Momentum"
            )

        if volumen_faktor >= 1.5:
            long_score += 20
            gruende_long.append(
                "stark erhöhtes Volumen"
            )

        elif volumen_faktor >= 1.1:
            long_score += 10
            gruende_long.append(
                "überdurchschnittliches Volumen"
            )

        if atr_prozent >= 3:
            long_score += 15
            gruende_long.append(
                "hohe handelbare Schwankung"
            )

        elif atr_prozent >= 2:
            long_score += 8

        # ----------------------------------------------------
        # SHORT / ABWÄRTS
        # ----------------------------------------------------

        if trend_abwaerts:
            short_score += 25
            gruende_short.append(
                "Abwärtstrend unter SMA20/SMA50"
            )

        if momentum20 <= -15:
            short_score += 25
            gruende_short.append(
                "stark negatives 20-Tage-Momentum"
            )

        elif momentum20 <= -5:
            short_score += 15
            gruende_short.append(
                "negatives 20-Tage-Momentum"
            )

        if volumen_faktor >= 1.5:
            short_score += 20
            gruende_short.append(
                "stark erhöhtes Volumen"
            )

        elif volumen_faktor >= 1.1:
            short_score += 10

        if atr_prozent >= 3:
            short_score += 15
            gruende_short.append(
                "hohe handelbare Schwankung"
            )

        # ====================================================
        # TAKE-PROFIT
        # ====================================================

        take_profit_score = 0
        gruende_tp = []

        if trend_aufwaerts:
            take_profit_score += 20
            gruende_tp.append(
                "Aufwärtstrend"
            )

        if momentum20 >= 15:
            take_profit_score += 25
            gruende_tp.append(
                "starke Kursbewegung"
            )

        if abstand_hoch <= 3:
            take_profit_score += 30
            gruende_tp.append(
                "sehr nahe am 20-Tage-Hoch"
            )

        elif abstand_hoch <= 5:
            take_profit_score += 20
            gruende_tp.append(
                "nahe am 20-Tage-Hoch"
            )

        if volatilitaet20 >= 40:
            take_profit_score += 15
            gruende_tp.append(
                "hohe kurzfristige Volatilität"
            )

        if volumen_faktor >= 1.5:
            take_profit_score += 10
            gruende_tp.append(
                "erhöhtes Volumen"
            )

        take_profit_score = min(
            take_profit_score,
            100
        )

        # ====================================================
        # BESTES SIGNAL
        # ====================================================

        if take_profit_score >= 70:

            signal = "🟡 TAKE-PROFIT-KANDIDAT"
            score = take_profit_score
            gruende = gruende_tp

        elif long_score >= 65:

            signal = "🟢 LONG-KANDIDAT"
            score = long_score
            gruende = gruende_long

        elif short_score >= 65:

            signal = "🔴 ABWÄRTS-KANDIDAT"
            score = short_score
            gruende = gruende_short

        else:

            signal = "⚪ BEOBACHTEN"
            score = max(
                long_score,
                short_score,
                take_profit_score
            )
            gruende = []

        # ====================================================
        # ATR ORIENTIERUNG
        # ====================================================

        atr_oben = kurs + atr14
        atr_unten = kurs - atr14

        return {

            "symbol": symbol,
            "kurs": kurs,

            "score": score,
            "signal": signal,

            "sma20": sma20,
            "sma50": sma50,

            "atr": atr14,
            "atr_prozent": atr_prozent,

            "volatilitaet20": volatilitaet20,

            "momentum5": momentum5,
            "momentum20": momentum20,
            "momentum60": momentum60,

            "hoch20": hoch20,
            "tief20": tief20,

            "abstand_hoch": abstand_hoch,

            "volumen_faktor": volumen_faktor,

            "atr_oben": atr_oben,
            "atr_unten": atr_unten,

            "gruende": gruende
        }

    except Exception as e:

        print(
            f"Fehler bei {symbol}: {e}"
        )

        return None


def scanner():

    print()
    print("=" * 75)
    print("       AKTIEN KI SCANNER V3")
    print("       SWING / VOLATILITÄT / SIGNAL")
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

    # ========================================================
    # SORTIEREN
    # ========================================================

    ergebnisse.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # ========================================================
    # AUSGABE
    # ========================================================

    print()
    print("=" * 75)
    print("             TOP SWING-SIGNALE")
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
            f"Kurs:              "
            f"${daten['kurs']:.2f}"
        )

        print(
            f"Score:             "
            f"{daten['score']}/100"
        )

        print(
            f"Signal:            "
            f"{daten['signal']}"
        )

        print(
            f"ATR 14:            "
            f"${daten['atr']:.2f}"
        )

        print(
            f"ATR:               "
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
            f"Abstand Hoch:      "
            f"{daten['abstand_hoch']:.2f}%"
        )

        print(
            f"Volumen Faktor:    "
            f"{daten['volumen_faktor']:.2f}x"
        )

        print(
            f"ATR oben:          "
            f"${daten['atr_oben']:.2f}"
        )

        print(
            f"ATR unten:         "
            f"${daten['atr_unten']:.2f}"
        )

        if daten["gruende"]:

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
        "Hinweis: Die Signale sind "
        "technische Analyse und keine "
        "Garantie für Gewinne."
    )


if __name__ == "__main__":
    scanner()
