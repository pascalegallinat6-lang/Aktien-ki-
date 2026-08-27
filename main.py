import yfinance as yf
import pandas as pd
import numpy as np
import time

# ==========================================
# AKTIEN KI SCANNER – VOLATILITÄT
# Sucht Aktien mit starken, handelbaren
# Kursschwankungen und Momentum
# ==========================================

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

        if df.empty or len(df) < 30:
            return None

        # ------------------------------------------
        # KURSE
        # ------------------------------------------

        close = df["Close"]
        high = df["High"]
        low = df["Low"]
        volume = df["Volume"]

        aktueller_kurs = float(close.iloc[-1])

        # ------------------------------------------
        # TAGESRENDITEN
        # ------------------------------------------

        renditen = close.pct_change().dropna()

        volatilitaet_20 = (
            renditen.tail(20).std() * np.sqrt(252) * 100
        )

        volatilitaet_60 = (
            renditen.tail(60).std() * np.sqrt(252) * 100
        )

        # ------------------------------------------
        # ATR 14
        # ------------------------------------------

        vorheriger_close = close.shift(1)

        true_range = pd.concat(
            [
                high - low,
                (high - vorheriger_close).abs(),
                (low - vorheriger_close).abs()
            ],
            axis=1
        ).max(axis=1)

        atr_14 = true_range.rolling(14).mean().iloc[-1]

        atr_prozent = (
            float(atr_14) / aktueller_kurs * 100
        )

        # ------------------------------------------
        # MOMENTUM
        # ------------------------------------------

        kurs_5 = float(close.iloc[-6])
        kurs_20 = float(close.iloc[-21])
        kurs_60 = float(close.iloc[-61])

        momentum_5 = (aktueller_kurs / kurs_5 - 1) * 100
        momentum_20 = (aktueller_kurs / kurs_20 - 1) * 100
        momentum_60 = (aktueller_kurs / kurs_60 - 1) * 100

        # ------------------------------------------
        # HOCH / TIEF
        # ------------------------------------------

        hoch_20 = float(high.tail(20).max())
        tief_20 = float(low.tail(20).min())

        hoch_60 = float(high.tail(60).max())
        tief_60 = float(low.tail(60).min())

        abstand_hoch_20 = (
            (hoch_20 - aktueller_kurs)
            / aktueller_kurs
            * 100
        )

        abstand_tief_20 = (
            (aktueller_kurs - tief_20)
            / aktueller_kurs
            * 100
        )

        # ------------------------------------------
        # VOLUMEN
        # ------------------------------------------

        durchschnitt_volumen = (
            volume.tail(20).mean()
        )

        aktuelles_volumen = float(volume.iloc[-1])

        volumen_verhaeltnis = (
            aktuelles_volumen / durchschnitt_volumen
            if durchschnitt_volumen > 0
            else 0
        )

        # ------------------------------------------
        # SCORE
        # ------------------------------------------

        score = 0
        gruende = []

        # Volatilität
        if atr_prozent >= 5:
            score += 30
            gruende.append("sehr hohe tägliche Schwankung")
        elif atr_prozent >= 3:
            score += 24
            gruende.append("hohe tägliche Schwankung")
        elif atr_prozent >= 2:
            score += 16
            gruende.append("gute tägliche Schwankung")
        elif atr_prozent >= 1:
            score += 8

        # 20-Tage-Volatilität
        if volatilitaet_20 >= 50:
            score += 20
            gruende.append("sehr hohe kurzfristige Volatilität")
        elif volatilitaet_20 >= 35:
            score += 15
            gruende.append("hohe kurzfristige Volatilität")
        elif volatilitaet_20 >= 25:
            score += 10

        # Momentum
        if momentum_20 >= 15:
            score += 20
            gruende.append("starkes 20-Tage-Momentum")
        elif momentum_20 >= 7:
            score += 12
            gruende.append("positives 20-Tage-Momentum")
        elif momentum_20 > 0:
            score += 6

        # Volumen
        if volumen_verhaeltnis >= 1.5:
            score += 15
            gruende.append("deutlich erhöhtes Handelsvolumen")
        elif volumen_verhaeltnis >= 1.1:
            score += 8
            gruende.append("überdurchschnittliches Handelsvolumen")

        # Nähe zum 20-Tage-Hoch
        if 0 < abstand_hoch_20 <= 5:
            score += 15
            gruende.append("nahe am 20-Tage-Hoch")
        elif 5 < abstand_hoch_20 <= 10:
            score += 8

        # Zu geringe Bewegung vermeiden
        if abs(momentum_20) < 2 and atr_prozent < 1:
            score -= 15

        score = max(0, min(100, score))

        # ------------------------------------------
        # KLASSIFIZIERUNG
        # ------------------------------------------

        if score >= 75:
            signal = "🟢 HOHES SWING-POTENZIAL"
        elif score >= 60:
            signal = "🟢 INTERESSANT"
        elif score >= 45:
            signal = "🟡 BEOBACHTEN"
        else:
            signal = "🔴 WENIG POTENZIAL"

        # ------------------------------------------
        # ANALYTISCHE ATR-ZONE
        # ------------------------------------------

        atr_ziel = aktueller_kurs + float(atr_14)

        return {
            "symbol": symbol,
            "kurs": aktueller_kurs,
            "score": score,
            "signal": signal,
            "atr": float(atr_14),
            "atr_prozent": atr_prozent,
            "volatilitaet_20": volatilitaet_20,
            "momentum_5": momentum_5,
            "momentum_20": momentum_20,
            "momentum_60": momentum_60,
            "hoch_20": hoch_20,
            "tief_20": tief_20,
            "abstand_hoch_20": abstand_hoch_20,
            "volumen_verhaeltnis": volumen_verhaeltnis,
            "atr_ziel": atr_ziel,
            "gruende": gruende
        }

    except Exception as e:
        print(f"Fehler bei {symbol}: {e}")
        return None


def scanner():

    print()
    print("=" * 70)
    print("        AKTIEN KI SCANNER – SWING / VOLATILITÄT")
    print("=" * 70)
    print()

    ergebnisse = []

    for symbol in AKTIEN:

        print(f"Analysiere {symbol} ...")

        daten = hole_daten(symbol)

        if daten:
            ergebnisse.append(daten)

        time.sleep(0.5)

    ergebnisse.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    print()
    print("=" * 70)
    print("        TOP-AKTIEN MIT SCHWANKUNGSPOTENZIAL")
    print("=" * 70)

    for platz, daten in enumerate(
        ergebnisse,
        start=1
    ):

        print()
        print(f"#{platz} 📊 {daten['symbol']}")
        print(f"Kurs:              ${daten['kurs']:.2f}")
        print(f"Score:             {daten['score']}/100")
        print(f"Signal:            {daten['signal']}")
        print(
            f"ATR 14:            ${daten['atr']:.2f}"
        )
        print(
            f"ATR:               {daten['atr_prozent']:.2f}%"
        )
        print(
            f"Volatilität 20T:   "
            f"{daten['volatilitaet_20']:.2f}%"
        )
        print(
            f"Momentum 20T:      "
            f"{daten['momentum_20']:.2f}%"
        )
        print(
            f"Abstand Hoch:      "
            f"{daten['abstand_hoch_20']:.2f}%"
        )
        print(
            f"Volumen Faktor:    "
            f"{daten['volumen_verhaeltnis']:.2f}x"
        )

        print(
            f"ATR-Orientierung:  "
            f"${daten['atr_ziel']:.2f}"
        )

        if daten["gruende"]:
            print("Gründe:")

            for grund in daten["gruende"]:
                print(f"  • {grund}")

    print()
    print("=" * 70)
    print("Scanner beendet.")
    print("=" * 70)
    print()
    print(
        "Hinweis: Der Score ist ein Analysemodell "
        "und keine Gewinn- oder Kaufgarantie."
    )


if __name__ == "__main__":
    scanner()
