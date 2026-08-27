import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# ============================================================
# AKTIEN TRADING SCANNER V6
# ============================================================

AKTIEN = [
    # Technologie
    "NVDA", "AMD", "AVGO", "MU", "INTC", "QCOM",
    "ARM", "SMCI", "AAPL", "MSFT", "ORCL", "CRM",
    "ADBE", "PLTR", "META", "GOOGL", "AMZN", "NFLX",

    # Trading / Wachstum
    "TSLA", "MSTR", "COIN", "HOOD", "UBER", "SHOP",
    "SNOW", "CRWD", "PANW", "NET", "DDOG", "RBLX",

    # Finanzen
    "JPM", "BAC", "GS", "MS", "V", "MA", "PYPL",

    # Industrie / Energie
    "BA", "CAT", "GE", "XOM", "CVX", "COP",

    # Konsum
    "WMT", "COST", "NKE", "SBUX", "MCD",

    # Weitere liquide Aktien
    "DIS", "PFE", "MRK", "LLY", "TMO", "ABNB",
    "DASH", "SQ", "ROKU", "SOFI", "DKNG",
    "CVNA", "GME", "AMC"
]


# ============================================================
# WKN / ISIN DER WICHTIGSTEN AKTIEN
# ============================================================

WERTPAPIERE = {

    "NVDA": ("918422", "US67066G1040"),
    "AMD": ("863186", "US0079031078"),
    "AAPL": ("865985", "US0378331005"),
    "MSFT": ("870747", "US5949181045"),
    "AMZN": ("906866", "US0231351067"),
    "GOOGL": ("A14Y6F", "US02079K3059"),
    "META": ("A1JWVX", "US30303M1027"),

    "TSLA": ("A1CX3T", "US88160R1014"),
    "MSTR": ("A0J3ER", "US5949724083"),
    "COIN": ("A2QP7J", "US19260Q1076"),
    "PLTR": ("A2QA4J", "US69608A1088"),
    "NFLX": ("552484", "US64110L1061"),

    "AVGO": ("A2JG9Z", "US11135F1012"),
    "MU": ("869020", "US5951121038"),
    "INTC": ("855681", "US4581401001"),
    "QCOM": ("883121", "US7475251036"),
    "SMCI": ("A40MRM", "US86800U3023"),
    "ORCL": ("871460", "US68389X1054"),
    "CRM": ("A0B87V", "US79466L3024"),
    "ADBE": ("871981", "US00724F1012"),

    "JPM": ("850628", "US46647P1049"),
    "BAC": ("858388", "US0605051046"),
    "V": ("A0NC7B", "US92826C8394"),
    "MA": ("A0F602", "US57636Q1040"),

    "UBER": ("A2PHHG", "US90353T1007"),
    "SHOP": ("A14TJP", "CA82509L1076"),

    "XOM": ("852549", "US30231G1022"),
    "CVX": ("852552", "US1667641005"),

    "BA": ("850471", "US0970231058"),
    "CAT": ("850598", "US1491231015")
}


# ============================================================
# EINSTELLUNGEN
# ============================================================

PERIODE = "6mo"
TOP_AKTIEN = 10

MIN_ATR_PROZENT = 1.5
MIN_VOLATILITAET = 20


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

        if df.empty:
            return None

        if len(df) < 70:
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

    # ========================================================
    # SMA
    # ========================================================

    sma20 = float(
        close.rolling(20).mean().iloc[-1]
    )

    sma50 = float(
        close.rolling(50).mean().iloc[-1]
    )

    # ========================================================
    # ATR
    # ========================================================

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

    # ========================================================
    # MOMENTUM
    # ========================================================

    momentum5 = (
        kurs / float(close.iloc[-6]) - 1
    ) * 100

    momentum20 = (
        kurs / float(close.iloc[-21]) - 1
    ) * 100

    momentum60 = (
        kurs / float(close.iloc[-61]) - 1
    ) * 100

    # ========================================================
    # VOLATILITÄT
    # ========================================================

    renditen = close.pct_change()

    volatilitaet20 = (
        renditen.tail(20).std()
        * np.sqrt(252)
        * 100
    )

    # ========================================================
    # VOLUMEN
    # ========================================================

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
    # HOCH / TIEF
    # ========================================================

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

    abstand_tief = (
        (kurs - tief20)
        / tief20
    ) * 100

    # ========================================================
    # TREND
    # ========================================================

    trend_long = (
        kurs > sma20
        and sma20 > sma50
    )

    trend_short = (
        kurs < sma20
        and sma20 < sma50
    )

    # ========================================================
    # LONG SCORE
    # ========================================================

    long_score = 0
    long_gruende = []

    if kurs > sma20:

        long_score += 15

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
            "positives 5-Tage-Momentum"
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

    if volumen_faktor >= 1.2:

        long_score += 10

        long_gruende.append(
            "erhöhtes Volumen"
        )

    if atr_prozent >= MIN_ATR_PROZENT:

        long_score += 10

        long_gruende.append(
            "gute Schwankungsbreite"
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

        short_score += 15

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
            "negatives 5-Tage-Momentum"
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

    if volumen_faktor >= 1.2:

        short_score += 10

        short_gruende.append(
            "erhöhtes Volumen"
        )

    if atr_prozent >= MIN_ATR_PROZENT:

        short_score += 10

        short_gruende.append(
            "gute Schwankungsbreite"
        )

    short_score = min(
        short_score,
        100
    )

    # ========================================================
    # TAKE PROFIT
    # ========================================================

    take_profit_score = 0
    tp_gruende = []

    if momentum20 > 10:

        take_profit_score += 25

        tp_gruende.append(
            "starkes 20-Tage-Momentum"
        )

    if momentum5 > 3:

        take_profit_score += 20

        tp_gruende.append(
            "starke kurzfristige Bewegung"
        )

    if abstand_hoch <= 3:

        take_profit_score += 30

        tp_gruende.append(
            "sehr nahe am 20-Tage-Hoch"
        )

    elif abstand_hoch <= 5:

        take_profit_score += 20

        tp_gruende.append(
            "nahe am 20-Tage-Hoch"
        )

    if atr_prozent >= 3:

        take_profit_score += 15

        tp_gruende.append(
            "hohe Schwankungsbreite"
        )

    if volumen_faktor >= 1.5:

        take_profit_score += 10

        tp_gruende.append(
            "stark erhöhtes Volumen"
        )

    take_profit_score = min(
        take_profit_score,
        100
    )

    # ========================================================
    # SIGNAL
    # ========================================================

    if take_profit_score >= 70:

        signal = "🟡 TAKE PROFIT"

        score = take_profit_score

        gruende = tp_gruende

    elif long_score >= 75:

        signal = "🟢 STARKER LONG"

        score = long_score

        gruende = long_gruende

    elif long_score >= 60:

        signal = "🟢 LONG"

        score = long_score

        gruende = long_gruende

    elif short_score >= 75:

        signal = "🔴 STARKER SHORT"

        score = short_score

        gruende = short_gruende

    elif short_score >= 60:

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

    if signal in [
        "🟢 LONG",
        "🟢 STARKER LONG"
    ]:

        einstieg = kurs

        stop_loss = (
            kurs - atr * 1.2
        )

        ziel1 = (
            kurs + atr
        )

        ziel2 = (
            kurs + atr * 2
        )

    elif signal in [
        "🔴 SHORT",
        "🔴 STARKER SHORT"
    ]:

        einstieg = kurs

        stop_loss = (
            kurs + atr * 1.2
        )

        ziel1 = (
            kurs - atr
        )

        ziel2 = (
            kurs - atr * 2
        )

    else:

        einstieg = kurs

        stop_loss = (
            kurs - atr
        )

        ziel1 = (
            kurs + atr
        )

        ziel2 = (
            kurs + atr * 2
        )

    # ========================================================
    # WKN / ISIN
    # ========================================================

    if ticker in WERTPAPIERE:

        wkn = WERTPAPIERE[ticker][0]
        isin = WERTPAPIERE[ticker][1]

    else:

        wkn = "nicht hinterlegt"
        isin = "nicht hinterlegt"

    return {

        "ticker": ticker,

        "wkn": wkn,

        "isin": isin,

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

        "einstieg":
            einstieg,

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

def ausgabe(x, nummer):

    print()
    print("=" * 70)

    print(
        f"#{nummer}  📊 {x['ticker']}"
    )

    print("-" * 70)

    print(
        f"WKN:              {x['wkn']}"
    )

    print(
        f"ISIN:             {x['isin']}"
    )

    print(
        f"Kurs:             ${x['kurs']:.2f}"
    )

    print(
        f"Signal:           {x['signal']}"
    )

    print(
        f"Score:            {x['score']}/100"
    )

    print(
        f"LONG Score:       {x['long_score']}/100"
    )

    print(
        f"SHORT Score:      {x['short_score']}/100"
    )

    print()

    print(
        f"ATR:              ${x['atr']:.2f}"
    )

    print(
        f"ATR %:            {x['atr_prozent']:.2f}%"
    )

    print(
        f"Volatilität 20T:  "
        f"{x['volatilitaet20']:.2f}%"
    )

    print(
        f"Momentum 5T:      "
        f"{x['momentum5']:+.2f}%"
    )

    print(
        f"Momentum 20T:     "
        f"{x['momentum20']:+.2f}%"
    )

    print(
        f"Momentum 60T:     "
        f"{x['momentum60']:+.2f}%"
    )

    print(
        f"Volumen:          "
        f"{x['volumen_faktor']:.2f}x"
    )

    print(
        f"Abstand Hoch:     "
        f"{x['abstand_hoch']:.2f}%"
    )

    print()

    print("TRADING-ZONEN")

    print(
        f"Einstieg:         "
        f"${x['einstieg']:.2f}"
    )

    print(
        f"Stop-Loss:        "
        f"${x['stop_loss']:.2f}"
    )

    print(
        f"Take Profit 1:    "
        f"${x['ziel1']:.2f}"
    )

    print(
        f"Take Profit 2:    "
        f"${x['ziel2']:.2f}"
    )

    if x["gruende"]:

        print()

        print("GRÜNDE:")

        for grund in x["gruende"]:

            print(
                f"  • {grund}"
            )


# ============================================================
# HAUPTPROGRAMM
# ============================================================

def main():

    print()
    print("=" * 70)
    print("             AKTIEN TRADING SCANNER V6")
    print("=" * 70)

    print()

    print(
        f"Scan gestartet: "
        f"{datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
    )

    print(
        f"Aktien im Scan: {len(AKTIEN)}"
    )

    ergebnisse = []

    # ========================================================
    # SCANNEN
    # ========================================================

    for ticker in AKTIEN:

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

    # ========================================================
    # SORTIEREN
    # ========================================================

    ergebnisse.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # ========================================================
    # TOP 10
    # ========================================================

    print()
    print()
    print("=" * 70)
    print("              🏆 TOP 10 TRADING")
    print("=" * 70)

    for nummer, x in enumerate(
        ergebnisse[:TOP_AKTIEN],
        start=1
    ):

        ausgabe(
            x,
            nummer
        )

    # ========================================================
    # LONG
    # ========================================================

    long_liste = [
        x for x in ergebnisse
        if x["signal"] in [
            "🟢 LONG",
            "🟢 STARKER LONG"
        ]
    ]

    print()
    print()
    print("=" * 70)
    print("                  🟢 LONG")
    print("=" * 70)

    for x in long_liste[:10]:

        print(
            f"{x['ticker']:6} | "
            f"WKN {x['wkn']:8} | "
            f"{x['signal']:20} | "
            f"{x['score']:3}/100"
        )

    # ========================================================
    # SHORT
    # ========================================================

    short_liste = [
        x for x in ergebnisse
        if x["signal"] in [
            "🔴 SHORT",
            "🔴 STARKER SHORT"
        ]
    ]

    print()
    print()
    print("=" * 70)
    print("                  🔴 SHORT")
    print("=" * 70)

    for x in short_liste[:10]:

        print(
            f"{x['ticker']:6} | "
            f"WKN {x['wkn']:8} | "
            f"{x['signal']:20} | "
            f"{x['score']:3}/100"
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
    print("=" * 70)
    print("                🟡 TAKE PROFIT")
    print("=" * 70)

    for x in tp_liste[:10]:

        print(
            f"{x['ticker']:6} | "
            f"WKN {x['wkn']:8} | "
            f"Score {x['score']:3}/100 | "
            f"Hoch-Abstand "
            f"{x['abstand_hoch']:.2f}%"
        )

    # ========================================================
    # ABSCHLUSS
    # ========================================================

    print()
    print()
    print("=" * 70)

    print(
        f"Analysierte Aktien: "
        f"{len(ergebnisse)}"
    )

    print(
        "Scanner abgeschlossen."
    )

    print("=" * 70)

    print()
    print(
        "⚠️ Technische Analyse ist keine "
        "Garantie für Gewinne."
    )


if __name__ == "__main__":
    main()
