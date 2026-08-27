import yfinance as yf
import pandas as pd
import time

# ==========================================
# AKTIEN KI SCANNER
# ==========================================

AKTIEN = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "TSLA",
    "AVGO",
    "JPM",
    "V",
]


def hole_daten(ticker_symbol):
    """Holt Kurs- und Unternehmensdaten."""

    try:
        ticker = yf.Ticker(ticker_symbol)

        info = ticker.info
        historie = ticker.history(period="6mo", auto_adjust=True)

        if historie.empty:
            return None

        aktueller_kurs = historie["Close"].iloc[-1]

        # Kurs vor ca. 3 Monaten
        kurs_3m = historie["Close"].iloc[
            max(0, len(historie) - 63)
        ]

        # Kurs vor ca. 6 Monaten
        kurs_6m = historie["Close"].iloc[0]

        performance_3m = ((aktueller_kurs / kurs_3m) - 1) * 100
        performance_6m = ((aktueller_kurs / kurs_6m) - 1) * 100

        return {
            "ticker": ticker_symbol,
            "kurs": aktueller_kurs,
            "performance_3m": performance_3m,
            "performance_6m": performance_6m,
            "pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "profit_margin": info.get("profitMargins"),
            "roe": info.get("returnOnEquity"),
            "revenue_growth": info.get("revenueGrowth"),
            "earnings_growth": info.get("earningsGrowth"),
            "market_cap": info.get("marketCap"),
        }

    except Exception as e:
        print(f"Fehler bei {ticker_symbol}: {e}")
        return None


def berechne_score(daten):
    """Berechnet einen einfachen Aktien-Score von 0 bis 100."""

    score = 0
    gruende = []

    # ------------------------------------------
    # MOMENTUM
    # ------------------------------------------

    if daten["performance_3m"] > 10:
        score += 20
        gruende.append("starkes 3-Monats-Momentum")
    elif daten["performance_3m"] > 0:
        score += 10
        gruende.append("positives Momentum")

    if daten["performance_6m"] > 15:
        score += 15
        gruende.append("starke 6-Monats-Performance")
    elif daten["performance_6m"] > 0:
        score += 7

    # ------------------------------------------
    # BEWERTUNG
    # ------------------------------------------

    pe = daten["pe"]

    if pe is not None:
        if 0 < pe < 20:
            score += 20
            gruende.append("vergleichsweise günstige Bewertung")
        elif 20 <= pe < 30:
            score += 10
        elif pe > 60:
            score -= 10
            gruende.append("hohe Bewertung")

    # ------------------------------------------
    # PROFITABILITÄT
    # ------------------------------------------

    margin = daten["profit_margin"]

    if margin is not None:
        if margin > 0.20:
            score += 15
            gruende.append("hohe Gewinnmarge")
        elif margin > 0.10:
            score += 8

    roe = daten["roe"]

    if roe is not None:
        if roe > 0.20:
            score += 10
            gruende.append("starke Eigenkapitalrendite")
        elif roe > 0.10:
            score += 5

    # ------------------------------------------
    # WACHSTUM
    # ------------------------------------------

    revenue_growth = daten["revenue_growth"]

    if revenue_growth is not None:
        if revenue_growth > 0.15:
            score += 10
            gruende.append("starkes Umsatzwachstum")
        elif revenue_growth > 0:
            score += 5

    earnings_growth = daten["earnings_growth"]

    if earnings_growth is not None:
        if earnings_growth > 0.15:
            score += 10
            gruende.append("starkes Gewinnwachstum")
        elif earnings_growth > 0:
            score += 5

    # Score begrenzen
    score = max(0, min(score, 100))

    # ------------------------------------------
    # BEWERTUNG
    # ------------------------------------------

    if score >= 75:
        bewertung = "🟢 SEHR INTERESSANT"
    elif score >= 60:
        bewertung = "🟢 INTERESSANT"
    elif score >= 45:
        bewertung = "🟡 BEOBACHTEN"
    else:
        bewertung = "🔴 SCHWACH"

    return score, bewertung, gruende


def scanner():
    print()
    print("=" * 60)
    print("       AKTIEN KI SCANNER")
    print("=" * 60)
    print()

    ergebnisse = []

    for aktie in AKTIEN:

        print(f"Analysiere {aktie} ...")

        daten = hole_daten(aktie)

        if daten is None:
            continue

        score, bewertung, gruende = berechne_score(daten)

        daten["score"] = score
        daten["bewertung"] = bewertung
        daten["gruende"] = gruende

        ergebnisse.append(daten)

        # Kleine Pause gegen zu viele Anfragen
        time.sleep(1)

    # Nach Score sortieren
    ergebnisse.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    print()
    print("=" * 60)
    print("ERGEBNIS")
    print("=" * 60)

    for daten in ergebnisse:

        print()
        print(f"📊 {daten['ticker']}")
        print(f"Kurs:       ${daten['kurs']:.2f}")
        print(f"Score:      {daten['score']}/100")
        print(f"Bewertung:  {daten['bewertung']}")
        print(
            f"3 Monate:   {daten['performance_3m']:.2f}%"
        )
        print(
            f"6 Monate:   {daten['performance_6m']:.2f}%"
        )

        if daten["pe"] is not None:
            print(f"KGV:        {daten['pe']:.2f}")

        if daten["gruende"]:
            print("Gründe:")

            for grund in daten["gruende"]:
                print(f"  • {grund}")

    print()
    print("=" * 60)
    print("Scanner beendet.")
    print("=" * 60)


if __name__ == "__main__":
    scanner()
