import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# ============================================================
# AKTIEN KI SCANNER V5
# LONG / SHORT / TAKE PROFIT
# ============================================================

WERTPAPIERE = {

    "NVDA": {
        "name": "NVIDIA",
        "wkn": "918422",
        "isin": "US67066G1040"
    },

    "TSLA": {
        "name": "Tesla",
        "wkn": "A1CX3T",
        "isin": "US88160R1014"
    },

    "AMD": {
        "name": "AMD",
        "wkn": "863186",
        "isin": "US0079031078"
    },

    "MSTR": {
        "name": "Strategy",
        "wkn": "A0J3ER",
        "isin": "US5949724083"
    },

    "COIN": {
        "name": "Coinbase",
        "wkn": "A2QP7J",
        "isin": "US19260Q1076"
    },

    "PLTR": {
        "name": "Palantir",
        "wkn": "A2QA4J",
        "isin": "US69608A1088"
    },

    "NFLX": {
        "name": "Netflix",
        "wkn": "552484",
        "isin": "US64110L1061"
    },

    "META": {
        "name": "Meta Platforms",
        "wkn": "A1JWVX",
        "isin": "US30303M1027"
    },

    "AMZN": {
        "name": "Amazon",
        "wkn": "906866",
        "isin": "US0231351067"
    },

    "GOOGL": {
        "name": "Alphabet A",
        "wkn": "A14Y6F",
        "isin": "US02079K3059"
    },

    "AAPL": {
        "name": "Apple",
        "wkn": "865985",
        "isin": "US0378331005"
    },

    "MSFT": {
        "name": "Microsoft",
        "wkn": "870747",
        "isin": "US5949181045"
    },

    "AVGO": {
        "name": "Broadcom",
        "wkn": "A2JG9Z",
        "isin": "US11135F1012"
    },

    "MU": {
        "name": "Micron",
        "wkn": "869020",
        "isin": "US5951121038"
    },

    "SMCI": {
        "name": "Super Micro Computer",
        "wkn": "A40MRM",
        "isin": "US86800U3023"
    },

    "JPM": {
        "name": "JPMorgan",
        "wkn": "850628",
        "isin": "US46647P1049"
    },

    "BAC": {
        "name": "Bank of America",
        "wkn": "858388",
        "isin": "US0605051046"
    },

    "XOM": {
        "name": "Exxon Mobil",
        "wkn": "852549",
        "isin": "US30231G1022"
    },

    "CVX": {
        "name": "Chevron",
        "wkn": "852552",
        "isin": "US1667641005"
    },

    "CAT": {
        "name": "Caterpillar",
        "wkn": "850598",
        "isin": "US1491231015"
    },

    "BA": {
        "name": "Boeing",
        "wkn": "850471",
        "isin": "US0970231058"
    },

    "UBER": {
        "name": "Uber",
        "wkn": "A2PHHG",
        "isin": "US90353T1007"
    },

    "SHOP": {
        "name": "Shopify",
        "wkn": "A14TJP",
        "isin": "CA82509L1076"
    },

    "ORCL": {
        "name": "Oracle",
        "wkn": "871460",
        "isin": "US68389X1054"
    },

    "CRM": {
        "name": "Salesforce",
        "wkn": "A0B87V",
        "isin": "US79466L3024"
    },

    "ADBE": {
        "name": "Adobe",
        "wkn": "871981",
        "isin": "US00724F1012"
    },

    "QCOM": {
        "name": "Qualcomm",
        "wkn": "883121",
        "isin": "US7475251036"
    },

    "INTC": {
        "name": "Intel",
        "wkn": "855681",
        "isin": "US4581401001"
    },

    "ARM": {
        "name": "Arm Holdings",
        "wkn": "A3EUCD",
        "isin": "US0420682058"
    },

    "HOOD": {
        "name": "Robinhood",
        "wkn": "A3CVQC",
        "isin": "US7707001027"
    }
}


# ============================================================
# EINSTELLUNGEN
# ============================================================

PERIODE = "6mo"

MIN_ATR = 2.0
MIN_VOLATILITAET = 25.0

# ============================================================
# KURSDATEN
# ============================================================

def hole_daten(ticker):

    try:

        aktie = yf.Ticker(ticker)

        df = aktie.history(
            period=PERIODE,
            interval="1d",
            auto_adjust=True
        )

        if df.empty or len(df) < 70:
            return None

        return df.dropna()

    except Exception as e:

        print(
            f"Fehler bei {ticker}: {e}"
        )

        return None


# ============================================================
# ANALYSE
# ============================================================

def analysiere(ticker, df):

    close = df["Close"]
    high = df["High"]
    low = df["Low"]
    volume = df["Volume"]

    kurs = float(close.iloc[-1])

    # --------------------------------------------------------
    # SMA
    # --------------------------------------------------------

    sma20 = float(
        close.rolling(20).mean().iloc[-1]
    )

    sma50 = float(
        close.rolling(50).mean().iloc[-1]
    )

    # --------------------------------------------------------
    # ATR
    # --------------------------------------------------------

    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs()
        ],
        axis=1
    ).max(axis=1)

    atr = float(
        true_range.rolling(14).mean().iloc[-1]
    )

    atr_prozent = (
        atr / kurs
    ) * 100

    # --------------------------------------------------------
    # MOMENTUM
    # --------------------------------------------------------

    momentum5 = (
        kurs / float(close.iloc[-6]) - 1
    ) * 100

    momentum20 = (
        kurs / float(close.iloc[-21]) - 1
    ) * 100

    momentum60 = (
        kurs / float(close.iloc[-61]) - 1
    ) * 100

    # --------------------------------------------------------
    # VOLATILITÄT
    # --------------------------------------------------------

    renditen = close.pct_change()

    volatilitaet20 = (
        renditen.tail(20).std()
        * np.sqrt(252)
        * 100
    )

    # --------------------------------------------------------
    # HOCH / TIEF
    # --------------------------------------------------------

    hoch20 = float(
        high.tail(20).max()
    )

    tief20 = float(
        low.tail(20).min()
    )

    abstand_hoch = (
        (hoch20 - kurs)
        / hoch20
    ) * 100

    # --------------------------------------------------------
    # VOLUMEN
    # --------------------------------------------------------

    durchschnitt_volumen = float(
        volume.tail(20).mean()
    )

    if durchschnitt_volumen > 0:

        volumen_faktor = (
            float(volume.iloc[-1])
            / durchschnitt_volumen
        )

    else:

        volumen_faktor = 0

    # ========================================================
    # LONG SCORE
    # ========================================================

    long_score = 0
    long_gruende = []

    if kurs > sma20:

        long_score += 20

        long_gruende.append(
            "Kurs über SMA20"
        )

    if sma20 > sma50:

        long_score += 20

        long_gruende.append(
            "SMA20 über SMA50"
        )

    if momentum5 > 2:

        long_score += 10

        long_gruende.append(
            "positives kurzfristiges Momentum"
        )

    if momentum20 > 5:

        long_score += 20

        long_gruende.append(
            "positives 20-Tage-Momentum"
        )

    if momentum60 > 10:

        long_score += 10

        long_gruende.append(
            "positives 60-Tage-Momentum"
        )

    if volumen_faktor > 1.2:

        long_score += 10

        long_gruende.append(
            "überdurchschnittliches Volumen"
        )

    if atr_prozent >= MIN_ATR:

        long_score += 10

        long_gruende.append(
            "ausreichende Schwankungsbreite"
        )

    long_score = min(
        long_score,
        100
    )

    # ========================================================
    # SHORT SCORE
    # ========================================================

    short_score = 0
    short_gruende = []

    if kurs < sma20:

        short_score += 20

        short_gruende.append(
            "Kurs unter SMA20"
        )

    if sma20 < sma50:

        short_score += 20

        short_gruende.append(
            "SMA20 unter SMA50"
        )

    if momentum5 < -2:

        short_score += 10

        short_gruende.append(
            "negatives kurzfristiges Momentum"
        )

    if momentum20 < -5:

        short_score += 20

        short_gruende.append(
            "negatives 20-Tage-Momentum"
        )

    if momentum60 < -10:

        short_score += 10

        short_gruende.append(
            "negatives 60-Tage-Momentum"
        )

    if volumen_faktor > 1.2:

        short_score += 10

        short_gruende.append(
            "überdurchschnittliches Volumen"
        )

    if atr_prozent >= MIN_ATR:

        short_score += 10

        short_gruende.append(
            "ausreichende Schwankungsbreite"
        )

    short_score = min(
        short_score,
        100
    )

    # ========================================================
    # TAKE PROFIT
    # ========================================================

    take_profit_score = 0
    take_profit_gruende = []

    if momentum20 > 10:

        take_profit_score += 25

        take_profit_gruende.append(
            "starkes 20-Tage-Momentum"
        )

    if momentum5 > 3:

        take_profit_score += 20

        take_profit_gruende.append(
            "starke kurzfristige Bewegung"
        )

    if abstand_hoch <= 3:

        take_profit_score += 30

        take_profit_gruende.append(
            "sehr nahe am 20-Tage-Hoch"
        )

    elif abstand_hoch <= 5:

        take_profit_score += 20

        take_profit_gruende.append(
            "nahe am 20-Tage-Hoch"
        )

    if atr_prozent >= 3:

        take_profit_score += 15

        take_profit_gruende.append(
            "hohe Schwankungsbreite"
        )

    if volumen_faktor >= 1.5:

        take_profit_score += 10

        take_profit_gruende.append(
            "stark erhöhtes Volumen"
        )

    take_profit_score = min(
        take_profit_score,
        100
    )

    # ========================================================
    # SIGNAL BESTIMMEN
    # ========================================================

    if take_profit_score >= 70:

        signal = "🟡 TAKE PROFIT"

        score = take_profit_score

        gruende = take_profit_gruende

    elif long_score >= 65:

        signal = "🟢 LONG"

        score = long_score

        gruende = long_gruende

    elif short_score >= 65:

        signal = "🔴 SHORT"

        score = short_score

        gruende = short_gruende

    else:

        signal = "⚪ BEOBACHTEN"

        score = max(
            long_score,
            short_score,
            take_profit_score
        )

        gruende = []

    # ========================================================
    # TECHNISCHE ZONEN
    # ========================================================

    if signal == "🟢 LONG":

        einstieg_unten = kurs - (
            atr * 0.50
        )

        einstieg_oben = kurs + (
            atr * 0.20
        )

        stop_loss = kurs - (
            atr * 1.20
        )

        ziel1 = kurs + (
            atr * 1.00
        )

        ziel2 = kurs + (
            atr * 2.00
        )

    elif signal == "🔴 SHORT":

        einstieg_unten = kurs - (
            atr * 0.20
        )

        einstieg_oben = kurs + (
            atr * 0.50
        )

        stop_loss = kurs + (
            atr * 1.20
        )

        ziel1 = kurs - (
            atr * 1.00
        )

        ziel2 = kurs - (
            atr * 2.00
        )

    else:

        einstieg_unten = kurs - (
            atr * 0.50
        )

        einstieg_oben = kurs + (
            atr * 0.50
        )

        stop_loss = kurs - atr

        ziel1 = kurs + atr

        ziel2 = kurs + (
            atr * 2
        )

    # ========================================================
    # WKN / ISIN
    # ========================================================

    info = WERTPAPIERE[ticker]

    return {

        "ticker": ticker,

        "name": info["name"],

        "wkn": info["wkn"],

        "isin": info["isin"],

        "kurs": kurs,

        "signal": signal,

        "score": score,

        "long_score": long_score,

        "short_score": short_score,

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

        "volumen_faktor":
            volumen_faktor,

        "abstand_hoch":
            abstand_hoch,

        "einstieg_unten":
            einstieg_unten,

        "einstieg_oben":
            einstieg_oben,

        "stop_loss":
            stop_loss,

        "ziel1":
            ziel1,

        "ziel2":
            ziel2,

        "gruende":
            gruende
    }


# ============================================================
# AUSGABE
# ============================================================

def zeige(ergebnis, nummer):

    print()
    print("=" * 65)

    print(
        f"#{nummer}  "
        f"{ergebnis['ticker']} – "
        f"{ergebnis['name']}"
    )

    print("-" * 65)

    print(
        f"WKN:              "
        f"{ergebnis['wkn']}"
    )

    print(
        f"ISIN:             "
        f"{ergebnis['isin']}"
    )

    print(
        f"Kurs:             "
        f"${ergebnis['kurs']:.2f}"
    )

    print(
        f"Signal:           "
        f"{ergebnis['signal']}"
    )

    print(
        f"Score:            "
        f"{ergebnis['score']}/100"
    )

    print(
        f"LONG Score:       "
        f"{ergebnis['long_score']}/100"
    )

    print(
        f"SHORT Score:      "
        f"{ergebnis['short_score']}/100"
    )

    print()

    print(
        f"ATR:              "
        f"${ergebnis['atr']:.2f}"
    )

    print(
        f"ATR %:            "
        f"{ergebnis['atr_prozent']:.2f}%"
    )

    print(
        f"Volatilität 20T:  "
        f"{ergebnis['volatilitaet20']:.2f}%"
    )

    print(
        f"Momentum 5T:      "
        f"{ergebnis['momentum5']:.2f}%"
    )

    print(
        f"Momentum 20T:     "
        f"{ergebnis['momentum20']:.2f}%"
    )

    print(
        f"Momentum 60T:     "
        f"{ergebnis['momentum60']:.2f}%"
    )

    print(
        f"Volumen:          "
        f"{ergebnis['volumen_faktor']:.2f}x"
    )

    print(
        f"Abstand Hoch:     "
        f"{ergebnis['abstand_hoch']:.2f}%"
    )

    print()

    print("TECHNISCHE ZONEN")

    print(
        f"Einstieg:         "
        f"${ergebnis['einstieg_unten']:.2f}"
        f" – "
        f"${ergebnis['einstieg_oben']:.2f}"
    )

    print(
        f"Stop-Loss:        "
        f"${ergebnis['stop_loss']:.2f}"
    )

    print(
        f"Ziel 1:            "
        f"${ergebnis['ziel1']:.2f}"
    )

    print(
        f"Ziel 2:            "
        f"${ergebnis['ziel2']:.2f}"
    )

    if ergebnis["gruende"]:

        print()

        print("GRÜNDE:")

        for grund in ergebnis["gruende"]:

            print(
                f"  • {grund}"
            )


# ============================================================
# HAUPTSCANNER
# ============================================================

def main():

    print()
    print("=" * 65)
    print("             AKTIEN KI SCANNER V5")
    print("=" * 65)

    print(
        f"Start: "
        f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
    )

    print(
        f"Aktien im Scan: "
        f"{len(WERTPAPIERE)}"
    )

    ergebnisse = []

    for ticker in WERTPAPIERE:

        print(
            f"Scanne {ticker}...",
            flush=True
        )

        df = hole_daten(ticker)

        if df is None:
            continue

        ergebnis = analysiere(
            ticker,
            df
        )

        if ergebnis:
            ergebnisse.append(
                ergebnis
            )

    # --------------------------------------------------------
    # SORTIEREN
    # --------------------------------------------------------

    ergebnisse.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # --------------------------------------------------------
    # ERGEBNIS
    # --------------------------------------------------------

    print()
    print()
    print("=" * 65)
    print("                    TOP SIGNALS")
    print("=" * 65)

    for nummer, ergebnis in enumerate(
        ergebnisse[:15],
        start=1
    ):

        zeige(
            ergebnis,
            nummer
        )

    # ========================================================
    # LONG LISTE
    # ========================================================

    long_liste = [
        x for x in ergebnisse
        if x["signal"] == "🟢 LONG"
    ]

    print()
    print()
    print("=" * 65)
    print("                    🟢 LONG")
    print("=" * 65)

    for x in long_liste[:10]:

        print(
            f"{x['ticker']:6} | "
            f"WKN {x['wkn']:8} | "
            f"Score {x['score']:3}/100 | "
            f"Momentum {x['momentum20']:+.2f}%"
        )

    # ========================================================
    # SHORT LISTE
    # ========================================================

    short_liste = [
        x for x in ergebnisse
        if x["signal"] == "🔴 SHORT"
    ]

    print()
    print()
    print("=" * 65)
    print("                    🔴 SHORT")
    print("=" * 65)

    for x in short_liste[:10]:

        print(
            f"{x['ticker']:6} | "
            f"WKN {x['wkn']:8} | "
            f"Score {x['score']:3}/100 | "
            f"Momentum {x['momentum20']:+.2f}%"
        )

    # ========================================================
    # TAKE PROFIT
    # ========================================================

    tp_liste = [
        x for x in ergebnisse
        if x["signal"] == "🟡 TAKE PROFIT"
    ]

    print()
    print()
    print("=" * 65)
    print("                 🟡 TAKE PROFIT")
    print("=" * 65)

    for x in tp_liste[:10]:

        print(
            f"{x['ticker']:6} | "
            f"WKN {x['wkn']:8} | "
            f"Score {x['score']:3}/100 | "
            f"Abstand Hoch {x['abstand_hoch']:.2f}%"
        )

    print()
    print()
    print("=" * 65)
    print("Scanner abgeschlossen.")
    print("=" * 65)

    print()
    print(
        "⚠️ Technische Analyse – "
        "keine Garantie für Gewinne."
    )


if __name__ == "__main__":
    main()
