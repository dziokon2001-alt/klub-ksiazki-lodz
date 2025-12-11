import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
import os # <--- NOWY IMPORT, NIEZBĘDNY!

# --- KONFIGURACJA STRONY ---
st.set_page_config(page_title="Klub Książki DLR Łódź", page_icon="📚")
st.title("📚 Klub Książki DLR Łódź")

# --- ŁĄCZENIE Z GOOGLE SHEETS (POPRAWIONE) ---
@st.cache_resource
def polacz_z_arkuszem():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    
    try:
        # NOWA LOGIKA: Najpierw sprawdzamy, czy plik istnieje fizycznie (Lokalnie)
        if os.path.exists("tajne_hasla.json"):
            creds = ServiceAccountCredentials.from_json_keyfile_name("tajne_hasla.json", scope)
        
        # Jeśli pliku nie ma, zakładamy, że jesteśmy w chmurze (Streamlit Cloud)
        else:
            dane_json = json.loads(st.secrets["connections"]["plik_json"])
            creds = ServiceAccountCredentials.from_json_keyfile_dict(dane_json, scope)
            
        client = gspread.authorize(creds)
        sheet = client.open("KlubKsiazkiDB").sheet1
        return sheet
        
    except Exception as e:
        st.error(f"BŁĄD POŁĄCZENIA: {e}")
        return None

# Reszta kodu bez zmian...
arkusz = polacz_z_arkuszem()

if arkusz is None:
    st.stop()

# --- DALSZA CZĘŚĆ KODU (LOGIKA APLIKACJI) ---
try:
    dane = arkusz.get_all_records()
except Exception:
    dane = []

# --- BANER NA GÓRZE ---
ksiazka_miesiaca = None
autor_miesiaca = ""

for wiersz in dane:
    if wiersz.get('Status') == "Aktualnie czytana":
        ksiazka_miesiaca = wiersz.get('Tytuł')
        autor_miesiaca = wiersz.get('Autor')
        break 

if ksiazka_miesiaca:
    st.success(f"🔥 **AKTUALNIE CZYTAMY:** {ksiazka_miesiaca} ({autor_miesiaca})")
else:
    st.info("💡 Nie wybrano książki miesiąca.")

st.divider()

# --- TABELA ---
st.subheader("Półka z Książkami")
if dane:
    df = pd.DataFrame(dane)
    st.dataframe(df, use_container_width=True)
else:
    st.info("Baza jest pusta.")

# --- SIDEBAR (DODAWANIE) ---
st.sidebar.header("Dodaj nową książkę")
with st.sidebar.form("dodaj_form"):
    nowy_tytul = st.text_input("Tytuł")
    nowy_autor = st.text_input("Autor")
    nowy_wlasciciel = st.text_input("Właściciel")
    submit = st.form_submit_button("Zapisz")

    if submit and nowy_tytul:
        try:
            arkusz.append_row([nowy_tytul, nowy_autor, nowy_wlasciciel, "Dostępna"])
            st.toast("Zapisano!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Błąd zapisu: {e}")

# --- ZMIANA STATUSU ---
st.subheader("Zarządzanie")
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    tytuly = [wiersz['Tytuł'] for wiersz in dane] if dane else []
    wybrana = st.selectbox("Wybierz książkę", tytuly) if tytuly else None

with col2:
    statusy = ["Dostępna", "Wypożyczona", "Aktualnie czytana", "Zaginiona"]
    status = st.selectbox("Status", statusy)

with col3:
    st.write("")
    st.write("")
    if st.button("Aktualizuj") and wybrana:
        try:
            cell = arkusz.find(wybrana)
            arkusz.update_cell(cell.row, 4, status)
            st.success("Zaktualizowano!")
            st.cache_data.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Błąd: {e}")