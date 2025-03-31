# -*- coding: utf-8 -*-
VERSION = "0.7"
"""
Created on Thu Mar 31 08:12:26 2025
@author: otamm
"""

import streamlit as st
import pandas as pd
import sqlite3
from fpdf import FPDF
import os
from cryptography.fernet import Fernet # 🔐 für Verschlüsselung
import streamlit.components.v1 as components
import json # 🌐 Sprache auswählen und Übersetzung laden

sprachoptionen = {
    "de": "🇩🇪 Deutsch",
    "en": "🇬🇧 English",
    "fr": "🇫🇷 Français",
    "es": "🇪🇸 Español"
}

sichtbare_labels = list(sprachoptionen.values())
sprache_auswahl = st.selectbox("🌐 Sprache / Language", options=sichtbare_labels, index=0)
lang = [code for code, label in sprachoptionen.items() if label == sprache_auswahl][0]

def load_translation(lang):
    with open(f"02_Hilfsfunktionen/translations/{lang}.json", "r", encoding="utf-8") as f:
        return json.load(f)
t = load_translation(lang)

import wetterdienst
# st.write("Aktiv verwendete wetterdienst-Version:", wetterdienst.__version__)
# st.write("Wetterdienst-Modulpfad:", os.path.dirname(wetterdienst.__file__))

import polars as pl

# Zugriff über Secret
ADMIN_PASSWORT = st.secrets["admin_passwort"]
key = st.secrets["aes_key"].encode()
fernet = Fernet(key)

# ----------------------------------------
# 🔧 Hilfsfunktionen
# ----------------------------------------

# Verschlüsselung
def encrypt_database():
    key = st.secrets["aes_key"].encode()
    fernet = Fernet(key)

    with open("datenbank/betriebsdaten.db", "rb") as file:
        original = file.read()

    encrypted = fernet.encrypt(original)

    with open("datenbank/betriebsdaten_encrypted.db", "wb") as enc_file:
        enc_file.write(encrypted)

# Dezimal- und Tausender- Trennzeichen
def format_de(value, decimals=2, tausender="'"):
    if isinstance(value, (int, float)):
        s = f"{value:,.{decimals}f}"
        s = s.replace(",", "X").replace(".", ",").replace("X", tausender)
        return s
    return str(value)

# Sicherstellen, dass der Speicherordner existiert
if not os.path.exists("datenbank"):
    os.makedirs("datenbank")


db_path = "datenbank/betriebsdaten.db"
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Tabelle erstellen
cursor.execute('''
    CREATE TABLE IF NOT EXISTS betriebsdaten (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        standort TEXT,
        betreiber TEXT,
        kontaktperson TEXT,
        email TEXT,
        telefon TEXT,
        plz TEXT,
        ort TEXT,
        strasse TEXT,
        stromverbrauch REAL,
        betriebsstunden INTEGER,
        strompreis REAL,
        max_kälteleistung REAL,
        durchschn_kälteleistung REAL,
        wirkungsgrad REAL,
        volumenstrom REAL,
        temp_eintritt REAL,
        temp_austritt REAL,
        kosten REAL
    )
''')
conn.commit()

def generate_pdf(data):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, "Betriebsdaten-Bericht", ln=True, align="C")
    pdf.ln(10)
    for key, value in data.items():
        pdf.cell(200, 10, f"{key}: {value}", ln=True)
    pdf_path = "Betriebsbericht.pdf"
    pdf.output(pdf_path)
    return pdf_path

# Autocomplete für alle Formularfelder aktivieren
components.html("""
<script>
  // aktiviert autocomplete auf allen Input-Feldern
  document.querySelectorAll("input").forEach(el => el.setAttribute("autocomplete", "on"));
</script>
""", height=0)

st.title(t["app_title"])
# Info-Box Stil
st.markdown("""
<style>
.custom-info-box {
    padding: 1em;
    background-color: #172D43;
    color: #C7EBFF;
    border-radius: 5px;
    font-weight: normal;
    text-align: justify;
}
</style>
""", unsafe_allow_html=True)

# Sprachabhängiger Text
st.markdown(
    "<div class='custom-info-box'>" +
    "<br>".join(t["intro_box"].split("\n")) +
    "</div>",
    unsafe_allow_html=True
)

# 📌 Auswahl: Formular mit Beispieldaten füllen?
mit_beispieldaten = st.checkbox(t["example_data"], value=False)

# Web-App UI
st.header(t["section_title_main"])

# Robuste Zuweisung mit Fallback-Werten
(
    id_val, standort_val, betreiber_val, kontaktperson_val, email_val, telefon_val,
    plz_val, ort_val, strasse_val,
    stromverbrauch_val, betriebsstunden_val, strompreis_val,
    max_kälteleistung_val, durchschn_kälteleistung_val, wirkungsgrad_val,
    volumenstrom_val, temp_eintritt_val, temp_austritt_val, kosten_val
) = (None,) * 19

# 📥 Autoausfüllung bei Bedarf
standort_val = "Werk Nord" if mit_beispieldaten else standort_val or ""
betreiber_val = "Muster GmbH" if mit_beispieldaten else betreiber_val or ""
kontaktperson_val = "Martina Mustermann" if mit_beispieldaten else kontaktperson_val or ""
email_val = "technik@mustergmbh.de" if mit_beispieldaten else email_val or ""
telefon_val = "+49 123 12345678" if mit_beispieldaten else telefon_val or ""
plz_val = "12345" if mit_beispieldaten else plz_val or ""
ort_val = "Musterstadt" if mit_beispieldaten else ort_val or ""
strasse_val = "Musterstraße 1" if mit_beispieldaten else strasse_val or ""

stromverbrauch_val = 200000.0 if mit_beispieldaten else stromverbrauch_val if stromverbrauch_val is not None else 200000.0
betriebsstunden_val = 6000 if mit_beispieldaten else betriebsstunden_val if betriebsstunden_val is not None else 6000
strompreis_val = 0.32 if mit_beispieldaten else strompreis_val if strompreis_val is not None else 0.20
max_kälteleistung_val = 120.0 if mit_beispieldaten else max_kälteleistung_val if max_kälteleistung_val is not None else 120.0
durchschn_kälteleistung_val = 100.0 if mit_beispieldaten else durchschn_kälteleistung_val if durchschn_kälteleistung_val is not None else 100.0
wirkungsgrad_val = 3.0 if mit_beispieldaten else wirkungsgrad_val if wirkungsgrad_val is not None else 3.0
volumenstrom_val = 28.7 if mit_beispieldaten else volumenstrom_val if volumenstrom_val is not None else 28.7
temp_eintritt_val = 18.0 if mit_beispieldaten else temp_eintritt_val if temp_eintritt_val is not None else 18.0
temp_austritt_val = 15.0 if mit_beispieldaten else temp_austritt_val if temp_austritt_val is not None else 15.0


# Schrittweite definieren für bessere Nutzung mit Plus-/Minus-Schaltflächen
stromverbrauch_step = 50.0
betriebsstunden_step = 100
messung_step = 0.5
strompreis_step = 0.01
leistung_step = 5.0
eer_step = 0.1
temp_step = 0.5
volumen_step = 0.5

st.header(t["section_1"])
standort = st.text_input(t["site"], value=standort_val, help=t["tooltips"]["standort"])
betreiber = st.text_input(t["operator"], value=betreiber_val, help=t["tooltips"]["betreiber"])
kontaktperson = st.text_input(t["contact"], value=kontaktperson_val, help=t["tooltips"]["kontaktperson"])
email = st.text_input(t["email"], value=email_val, help=t["tooltips"]["email"])
telefon = st.text_input(t["phone"], value=telefon_val, help=t["tooltips"]["email"])
plz = st.text_input(t["postal_code"], value=plz_val, help=t["tooltips"]["plz"])
ort = st.text_input(t["city"], value=ort_val, help=t["tooltips"]["ort"])
strasse = st.text_input(t["street"], value=strasse_val, help=t["tooltips"]["strasse"])

st.header(t["section_2"])

betriebsstunden = st.number_input(t["input_hours_per_year"], min_value=0, max_value=8760, value=betriebsstunden_val, step=betriebsstunden_step, format="%d", help=t["tooltips"]["betriebsstunden"])
strompreis = st.number_input(t["input_power_price"], min_value=0.0, value=strompreis_val, step=strompreis_step, format="%0.2f", help=t["tooltips"]["strompreis"])

verbrauch_bekannt = st.radio(
    t["question_known_consumption"],
    (t["option_yes"], t["option_no"]),
    index=0,
    horizontal=True
)

if verbrauch_bekannt == t["option_yes"]:
    stromverbrauch = st.number_input(
        "Jahresstromverbrauch der Kältemaschine (kWh)",
        min_value=0.0,
        value=stromverbrauch_val,
        step=stromverbrauch_step,
        format="%0.0f",
        help=t["tooltips"]["stromverbrauch"]
    )
else:
    stromverbrauch = 0.0  # oder None, je nach späterer Verarbeitung

    ermitteln = st.checkbox(t["question_self_estimate"])

    if ermitteln:
        st.subheader("2.1 Messbasierte Verbrauchserfassung")
        st.info("💡 Tragen Sie hier den gemessenen Wert Stromverbrauch Kältemaschine (kWh) und die Dauer der Messung in Stunden ein.")

        messverbrauch = st.number_input(t["input_measured_consumption"], min_value=0.0, step=stromverbrauch_step, format="%0.0f", help=t["tooltips"]["messverbrauch"])
        messdauer = st.number_input(t["input_measurement_duration"], min_value=0.5, step=messung_step, format="%0.1f", help=t["tooltips"]["messdauer"])

        if messdauer > 0:
            leistung_messung = messverbrauch / messdauer
            st.write(f"🔹 Durchschnittliche elektrische Leistungsaufnahme: {format_de(leistung_messung, 0)} kW")
            berechnete_kaelteleistung = leistung_messung * wirkungsgrad_val
            st.write(f"🔹 resultierende durchschnittliche Kälteleistung: {format_de(berechnete_kaelteleistung, 1)} kW")
        else:
            durchschn_leistung = None
            st.warning("Bitte eine Messdauer > 0 angeben.")

            if betriebsstunden > 0:
                stromverbrauch = leistung_messung * betriebsstunden
                st.write(f"🔹 Jahresstromverbrauch (prognostiziert): {format_de(stromverbrauch, 0)} kWh")

st.header(t["section_3"])
st.info("💡 Maximale Kälteleistung laut Hersteller. Durchschnittswerte können geschätzt oder berechnet werden.")
max_kälteleistung = st.number_input("Nenn-Kälteleistung (kW) laut Datenblatt", min_value=0.0, value=max_kälteleistung_val, step=leistung_step, format="%0.1f", help=t["tooltips"]["max_kälteleistung"])
durchschn_kälteleistung = st.number_input("Durchschnittlich abgenommene Kälteleistung (kW), falls bekannt.", min_value=0.0, value=durchschn_kälteleistung_val, step=leistung_step, format="%0.1f", help=t["tooltips"]["durchschn_kälteleistung"])
wirkungsgrad = st.number_input("Wirkungsgrad (EER)", min_value=0.1, max_value=10.0, value=wirkungsgrad_val, step=eer_step, format="%0.1f", help=t["tooltips"]["wirkungsgrad"])

# Berechnung: Durchschnittliche Kälteleistung aus Stromverbrauch und Wirkungsgrad
# ➕ Absicherung gegen Division durch 0 bei Abweichungsberechnung
if wirkungsgrad > 0 and stromverbrauch > 0 and betriebsstunden > 0:
    berechnete_kälteleistung = stromverbrauch / betriebsstunden * wirkungsgrad
    st.write(f"🔹 Berechnete durchschnittliche Kälteleistung aus Jahresstromverbrauch und Betriebsstunden: {format_de(berechnete_kälteleistung, 1)} kW")

    if durchschn_kälteleistung > 0:
        differenz = abs(durchschn_kälteleistung - berechnete_kälteleistung)
        if berechnete_kälteleistung != 0:
            prozent_diff = differenz / berechnete_kälteleistung
            if prozent_diff < 0.05:
                st.success(f"✅ Unterschied zur Eingabe: {format_de(differenz, 1)} kW ({prozent_diff:.0%} Abweichung)")
            elif prozent_diff < 0.20:
                st.warning(f"⚠️ Unterschied zur Eingabe: {format_de(differenz, 1)} kW ({prozent_diff:.0%} Abweichung)")
            else:
                st.error(f"🚨 Starke Abweichung: {format_de(differenz, 1)} kW ({prozent_diff:.0%} Abweichung)")
        else:
            st.warning("Berechnete Kälteleistung ist 0 – kein Vergleich möglich.")
else:
    st.info(t["calc_not_possible"])



st.header(t["section_4"])
st.info("💡 Volumenstrom in m³/h und Temperaturen an Ein- und Austritt zur Berechnung der Leistung.")
volumenstrom = st.number_input("Volumenstrom (m³/h)", min_value=0.0, value=5.0, step=volumen_step, format="%0.1f")
temp_eintritt = st.number_input("Eintrittstemperatur (°C)", min_value=8.0, max_value=30.0, value=18.0, step=temp_step, format="%0.1f")
temp_austritt = st.number_input("Austrittstemperatur (°C)", min_value=4.0, max_value=25.0, value=15.0, step=temp_step, format="%0.1f")

delta_T = temp_eintritt - temp_austritt if temp_eintritt > temp_austritt else 0
leistung_temp = volumenstrom * 1.16 * delta_T if delta_T > 0 and volumenstrom > 0 else 0

if betriebsstunden > 0:
    kosten = stromverbrauch * strompreis
    st.write(f"🔹 **Jährliche Stromkosten:** {format_de(kosten, 0)} EUR")
else:
    kosten = None

if st.button(t["submit"]):
    cursor.execute('''
        INSERT INTO betriebsdaten (
            standort, betreiber, kontaktperson, email, telefon, plz, ort, strasse,
            stromverbrauch, betriebsstunden, strompreis,
            max_kälteleistung, durchschn_kälteleistung, wirkungsgrad,
            volumenstrom, temp_eintritt, temp_austritt,
            kosten
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        standort, betreiber, kontaktperson, email, telefon, plz, ort, strasse,
        stromverbrauch, betriebsstunden, strompreis,
        max_kälteleistung, durchschn_kälteleistung, wirkungsgrad,
        volumenstrom, temp_eintritt, temp_austritt,
        kosten
    ))
    conn.commit()
    st.session_state['eigene_id'] = cursor.lastrowid
    encrypt_database()  # 🔐 automatische Verschlüsselung
    st.success("✅ Daten wurden erfolgreich gespeichert und verschlüsselt!")



if st.button("Gespeicherte Daten anzeigen"):
    if 'eigene_id' in st.session_state:
        cursor.execute("SELECT * FROM betriebsdaten WHERE id = ?", (st.session_state['eigene_id'],))
        daten = cursor.fetchall()
        df = pd.DataFrame(daten, columns=[
            "ID", "Standort", "Betreiber", "Kontaktperson", "E-Mail", "Telefon", "PLZ", "Ort", "Strasse",
            "Stromverbrauch", "Betriebsstunden", "Strompreis", "Max. Kälteleistung",
            "Durchschn. Kälteleistung", "Wirkungsgrad", "Volumenstrom",
            "T Eintritt", "T Austritt", "Kosten"
            ])
        st.dataframe(df)
    else:
        st.info("Keine Daten in dieser Session gespeichert.")


if st.button(t["create_pdf"]):
    data = {
        "Standort": standort,
        "Betreiber": betreiber,
        "Kontaktperson": kontaktperson,
        "E-Mail": email,
        "Telefon": telefon,
        "PLZ": plz,
        "Ort": ort,
        "Strasse": strasse,
        "Stromverbrauch (kWh)": format_de(stromverbrauch, 0),
        "Betriebsstunden": format_de(betriebsstunden, 0),
        "Strompreis (EUR/kWh)": format_de(strompreis, 2),
        "Max. Kälteleistung (kW)": format_de(max_kälteleistung, 0),
        "Durchschn. Kälteleistung (kW)": format_de(durchschn_kälteleistung, 0),
        "Wirkungsgrad (EER)": format_de(wirkungsgrad, 1),
        "Volumenstrom (m³/h)": format_de(volumenstrom, 1),
        "Temperatur Eintritt (°C)": format_de(temp_eintritt, 1),
        "Temperatur Austritt (°C)": format_de(temp_austritt, 1),
        "Jährliche Kosten (EUR)": format_de(kosten, 0) if kosten is not None else "N/A",
    }
    pdf_path = generate_pdf(data)
    st.success("✅ PDF wurde erstellt!")
    with open(pdf_path, "rb") as file:
        st.download_button(t["download_pdf"], file, file_name="Betriebsbericht.pdf")

from wetterdienst.provider.dwd.observation import DwdObservationRequest
from geopy.geocoders import Nominatim
from datetime import datetime

@st.cache_data(show_spinner=False)
def get_coordinates_from_plz(plz_code):
    geolocator = Nominatim(user_agent="coolcalc")
    location = geolocator.geocode(f"{plz_code}, Germany")
    if location:
        return (location.latitude, location.longitude)
    return None

@st.cache_data(show_spinner=True)
def get_stationen_und_parameter(coords, entfernung_km):
    lat, lon = coords
    request = DwdObservationRequest(
        parameters="hourly/air_temperature",
        periods="historical",
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    stations = request.filter_by_distance((lat, lon), distance=entfernung_km)
    df_stations = stations.df

    stationen_mit_parametern = {}

    for station_id in df_stations["station_id"]:
        try:
            req = request.filter_by_station_id(station_id)
            df = req.values.all().df
            if df.shape[0] == 0:
                continue
            parameter_liste = df["parameter"].unique().to_list()
            if "temperature_air_mean_2m" in parameter_liste:
                stationen_mit_parametern[station_id] = {
                    "parameter": parameter_liste,
                    "daten": df
                }
        except Exception:
            continue

    return stationen_mit_parametern


# 🔄 Temperatur-Auswertung aus PLZ
if plz:
    coords = get_coordinates_from_plz(plz)
    if coords:
        entfernung = st.slider(t["weather_search_radius"], min_value=10, max_value=300, value=100, step=10)

        st.markdown("### Temperaturgrenzen definieren")
        temp_grenze_1 = st.number_input(t["weather_limit_1"], min_value=-50.0, max_value=60.0, value=12.0, step=0.5)
        temp_grenze_2 = st.number_input(t["weather_limit_2"], min_value=temp_grenze_1, max_value=60.0, value=21.0, step=0.5)
        temp_grenze_3 = st.number_input(t["weather_limit_3"], min_value=temp_grenze_2, max_value=60.0, value=30.0, step=0.5)

        with st.expander("📈 Außentemperatur-Auswertung 2023 (DWD)", expanded=False):
            with st.spinner("Stationen & Parameter werden geladen..."):
                try:
                    daten = get_stationen_und_parameter(coords, entfernung)
                    if daten:
                        stationen = list(daten.keys())
                        station_id = st.selectbox(t["weather_select_station"], stationen)
                        df_temp = daten[station_id]["daten"]
                        df_temp = df_temp.filter(pl.col("parameter") == "temperature_air_mean_2m")

                        st.success(f"Daten von Station {station_id} – Temperaturmittelwerte")

                        zählung = {
                            f"< {temp_grenze_1} °C": (df_temp["value"] < temp_grenze_1).sum(),
                            f"{temp_grenze_1} °C – <{temp_grenze_2} °C": ((df_temp["value"] >= temp_grenze_1) & (df_temp["value"] < temp_grenze_2)).sum(),
                            f"{temp_grenze_2} °C – <{temp_grenze_3} °C": ((df_temp["value"] >= temp_grenze_2) & (df_temp["value"] < temp_grenze_3)).sum(),
                            f"≥ {temp_grenze_3} °C": (df_temp["value"] >= temp_grenze_3).sum()
                        }

                        st.write(t["weather_distribution_title"])
                        for bereich, anzahl in zählung.items():
                            st.markdown(f"- **{bereich}**: {anzahl} Stunden")

                        st.line_chart(df_temp.rename({"date": "index"}).to_pandas().set_index("index")["value"])

                    else:
                        st.warning(t["weather_no_data"])
                except Exception as e:
                    st.error(f"Fehler beim Abrufen: {e}")

# 🔒 Entwicklerzugang: Gesicherter Datenbank-Download
query_params = st.query_params
# st.write("Query Params:", query_params)
admin_access = query_params.get("zugang", "") == "6T8wA7v9zQp1"   # sicherer Parameter


if admin_access:
    st.markdown("---")
    st.subheader(t["admin_title"])

    password = st.text_input(t["admin_password"], type="password")

    if password == ADMIN_PASSWORT:
        encrypted_path = "datenbank/betriebsdaten_encrypted.db"
        if os.path.exists(encrypted_path):
            with open(encrypted_path, "rb") as f:
                st.download_button(t["admin_download"], f, file_name="betriebsdaten_encrypted.db")
        else:
            st.warning("⚠️ Keine verschlüsselte Datenbank gefunden.")
    elif password != "":
        st.error("❌ Falsches Passwort.")

