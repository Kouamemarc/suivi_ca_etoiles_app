import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime

# -------------------- CONFIG GLOBALE --------------------

st.set_page_config(
    page_title="Dashboard Closes Amiens & Beauvais",
    layout="centered",  # un peu plus friendly mobile
    initial_sidebar_state="expanded",
)

# Fichier de données lu au lancement
DATA_PATH = "suivi_ca_etoile_v2.xlsx"  # doit être à côté de app.py


# -------------------- OBJECTIFS (avec valeurs par défaut) --------------------


def init_objectifs():
    if "objectifs" not in st.session_state:
        st.session_state["objectifs"] = {
            "CA_close": {
                "Amiens": 350.0,
                "Beauvais": 200.0,
            },
            "note_min": 4.5,
        }


init_objectifs()


# -------------------- FONCTIONS --------------------


@st.cache_data
def load_data_from_excel(path: str):
    try:
        xls = pd.ExcelFile(path)
    except FileNotFoundError:
        st.error(f"❌ Fichier de données introuvable : {path}")
        st.info(
            "Vérifie que le fichier est présent dans le même dossier que app.py "
            "et bien poussé sur GitHub / Streamlit Cloud."
        )
        st.stop()

    df_ca = pd.read_excel(xls, "CA_Close")
    df_notes = pd.read_excel(xls, "Évolution_Notes")

    df_ca["Date"] = pd.to_datetime(df_ca["Date"])
    df_notes["Date"] = pd.to_datetime(df_notes["Date"])
    return df_ca, df_notes


def compute_duration_hours(period_str: str) -> float:
    """Calcule la durée en heures à partir d'une chaîne du type '23:00 - 00:00'."""
    try:
        start_str, end_str = [s.strip() for s in period_str.split("-")]
    except Exception:
        return np.nan
    start = pd.to_datetime(start_str, format="%H:%M")
    end = pd.to_datetime(end_str, format="%H:%M")
    delta = (end - start).total_seconds() / 3600.0
    if delta <= 0:
        delta += 24.0
    return delta


def add_ca_horaire(df_ca: pd.DataFrame) -> pd.DataFrame:
    df = df_ca.copy()
    df["Duree (h)"] = df["Période de close"].apply(compute_duration_hours)
    df["CA horaire (€ / h)"] = df["Chiffre d’affaires (€)"] / df["Duree (h)"]
    df["Cmd horaires"] = df["Nombre commandes"] / df["Duree (h)"]
    return df


def build_excel_bytes(df_ca: pd.DataFrame, df_notes: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_ca.to_excel(writer, sheet_name="CA_Close", index=False)
        df_notes.to_excel(writer, sheet_name="Évolution_Notes", index=False)
    buffer.seek(0)
    return buffer.read()


def build_pdf_report(df_ca_f, df_notes_f, ville_sel, date_deb, date_fin):
    """
    Génère un PDF simple de synthèse (KPI & objectifs).
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 50
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, "Synthèse Closes Amiens & Beauvais")
    y -= 25
    c.setFont("Helvetica", 10)
    c.drawString(
        40,
        y,
        f"Période : {date_deb.strftime('%d/%m/%Y')} - {date_fin.strftime('%d/%m/%Y')}   |   Filtre ville : {ville_sel}",
    )
    y -= 30

    # Objectifs
    obj = st.session_state["objectifs"]
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Objectifs")
    y -= 18
    c.setFont("Helvetica", 10)
    c.drawString(
        50,
        y,
        f"CA close Amiens ≥ {obj['CA_close']['Amiens']} €  |  CA close Beauvais ≥ {obj['CA_close']['Beauvais']} €",
    )
    y -= 15
    c.drawString(50, y, f"Notes (Uber & Deliveroo) ≥ {obj['note_min']}")
    y -= 30

    # KPI CA
    if not df_ca_f.empty:
        total_ca = df_ca_f["Chiffre d’affaires (€)"].sum()
        total_cmd = df_ca_f["Nombre commandes"].sum()
        panier_moy = total_ca / total_cmd if total_cmd > 0 else np.nan

        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "KPI CA & commandes")
        y -= 18
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"CA total : {total_ca:.0f} €")
        y -= 15
        c.drawString(50, y, f"Nombre de commandes : {int(total_cmd)}")
        y -= 15
        c.drawString(
            50,
            y,
            f"Panier moyen : {panier_moy:.2f} €" if not np.isnan(panier_moy) else "Panier moyen : NA",
        )
        y -= 25

    # KPI notes
    if not df_notes_f.empty:
        moy_uber = df_notes_f["Note Uber Eats"].mean()
        moy_deliv = df_notes_f["Note Deliveroo"].mean()
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, "KPI Notes")
        y -= 18
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Note moyenne Uber Eats : {moy_uber:.2f}")
        y -= 15
        c.drawString(50, y, f"Note moyenne Deliveroo : {moy_deliv:.2f}")
        y -= 25

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# -------------------- CHARGEMENT DES DONNÉES --------------------


st.sidebar.title("⚙️ Paramètres")
st.sidebar.markdown("📡 Source des données : **fichier Excel du projet**")
st.sidebar.code(DATA_PATH, language="text")

if "df_ca" not in st.session_state or "df_notes" not in st.session_state:
    df_ca_raw, df_notes_raw = load_data_from_excel(DATA_PATH)
    st.session_state["df_ca"] = add_ca_horaire(df_ca_raw)
    st.session_state["df_notes"] = df_notes_raw.copy()

df_ca = st.session_state["df_ca"]
df_notes = st.session_state["df_notes"]

# -------------------- FILTRES GLOBAUX --------------------

mode = st.sidebar.selectbox(
    "Mode",
    ["Analyse", "Objectifs", "Saisie des données"],
    help="Analyse = dashboard, Objectifs = configuration, Saisie = ajout de données.",
)

villes = ["Toutes"] + sorted(df_ca["Ville"].dropna().unique().tolist())
ville_sel = st.sidebar.selectbox("Ville", villes)

min_date = min(df_ca["Date"].min(), df_notes["Date"].min())
max_date = max(df_ca["Date"].max(), df_notes["Date"].max())
date_deb, date_fin = st.sidebar.date_input(
    "Période d'analyse",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(),
    max_value=max_date.date(),
)

objectifs = st.session_state["objectifs"]

# -------------------- MODE OBJECTIFS --------------------

if mode == "Objectifs":
    st.title("🎯 Paramétrage des objectifs")

    st.markdown("## Objectifs CA close par ville")

    col1, col2 = st.columns(2)
    with col1:
        obj_amiens = st.number_input(
            "Objectif CA close Amiens (€)",
            min_value=0.0,
            step=10.0,
            value=float(objectifs["CA_close"]["Amiens"]),
        )
    with col2:
        obj_beauvais = st.number_input(
            "Objectif CA close Beauvais (€)",
            min_value=0.0,
            step=10.0,
            value=float(objectifs["CA_close"]["Beauvais"]),
        )

    st.markdown("## Objectif notes (étoiles)")

    obj_note = st.number_input(
        "Objectif note minimale (Uber & Deliveroo)",
        min_value=0.0,
        max_value=5.0,
        step=0.1,
        value=float(objectifs["note_min"]),
    )

    if st.button("💾 Enregistrer les objectifs pour cette session"):
        st.session_state["objectifs"]["CA_close"]["Amiens"] = obj_amiens
        st.session_state["objectifs"]["CA_close"]["Beauvais"] = obj_beauvais
        st.session_state["objectifs"]["note_min"] = obj_note
        st.success("✅ Objectifs mis à jour pour cette session.")

    st.info(
        "Ces objectifs sont mémorisés tant que ta session Streamlit reste ouverte. "
        "Pour une persistance plus longue, on pourra plus tard les stocker dans un Google Sheets ou une base."
    )

# -------------------- MODE ANALYSE --------------------

elif mode == "Analyse":
    section = st.sidebar.radio(
        "Section",
        ["CA & commandes closes", "Évolution des notes (étoiles)"],
    )

    # filtres de base
    mask_dates_ca = (df_ca["Date"] >= pd.to_datetime(date_deb)) & (
        df_ca["Date"] <= pd.to_datetime(date_fin)
    )
    mask_dates_notes = (df_notes["Date"] >= pd.to_datetime(date_deb)) & (
        df_notes["Date"] <= pd.to_datetime(date_fin)
    )

    df_ca_f = df_ca[mask_dates_ca].copy()
    df_notes_f = df_notes[mask_dates_notes].copy()

    if ville_sel != "Toutes":
        df_ca_f = df_ca_f[df_ca_f["Ville"] == ville_sel]
        df_notes_f = df_notes_f[df_notes_f["Ville"] == ville_sel]

    # --------- PAGE CA / COMMANDES ---------
    if section == "CA & commandes closes":
        st.title("📊 CA & Nombre de commandes – Closes")

        if df_ca_f.empty:
            st.warning("Aucune donnée pour les filtres sélectionnés.")
            st.stop()

        total_ca = df_ca_f["Chiffre d’affaires (€)"].sum()
        total_cmd = df_ca_f["Nombre commandes"].sum()
        panier_moy = total_ca / total_cmd if total_cmd > 0 else np.nan
        ca_horaire_moy = df_ca_f["CA horaire (€ / h)"].mean()

        # Objectif CA pour la ville sélectionnée
        objectif_ca = None
        if ville_sel in objectifs["CA_close"]:
            objectif_ca = objectifs["CA_close"][ville_sel]

        # Statut objectif par ligne + % OK
        if objectif_ca is not None:
            df_ca_f["OK_objectif_CA"] = df_ca_f["Chiffre d’affaires (€)"] >= objectif_ca
            nb_ok = int(df_ca_f["OK_objectif_CA"].sum())
            nb_total = len(df_ca_f)
            pct_ok = 100 * nb_ok / nb_total if nb_total > 0 else 0
        else:
            nb_ok = nb_total = pct_ok = None

        col1, col2 = st.columns(2)
        col3, col4 = st.columns(2)

        col1.metric("CA total (€)", f"{total_ca:,.0f}".replace(",", " "))
        col2.metric("Nombre de commandes", int(total_cmd))
        col3.metric(
            "Panier moyen (€)",
            f"{panier_moy:.2f}" if not np.isnan(panier_moy) else "NA",
        )
        col4.metric(
            "CA horaire moyen (€ / h)",
            f"{ca_horaire_moy:.2f}" if not np.isnan(ca_horaire_moy) else "NA",
        )

        if objectif_ca is not None:
            emoji = "🟢" if pct_ok >= 80 else "🟡" if pct_ok >= 50 else "🔴"
            st.markdown(
                f"**Objectif CA close {ville_sel} : {objectif_ca} € par close**  "
                f"→ Closes ≥ objectif : **{nb_ok} / {nb_total}** ({pct_ok:.1f} %) {emoji}"
            )

        st.markdown("### 🏆 Top périodes de close (par CA horaire)")
        top_periods = (
            df_ca_f.groupby(
                ["Ville", "Période de close"], as_index=False
            )[["CA horaire (€ / h)", "Chiffre d’affaires (€)", "Nombre commandes"]]
            .mean(numeric_only=True)
            .sort_values("CA horaire (€ / h)", ascending=False)
        )
        st.dataframe(top_periods.head(10), use_container_width=True)

        st.markdown("### 📆 Évolution du CA par période de close")
        pivot_ca = (
            df_ca_f.groupby(
                ["Date", "Ville", "Période de close"], as_index=False
            )[
                [
                    "Chiffre d’affaires (€)",
                    "Nombre commandes",
                    "CA horaire (€ / h)",
                    "Cmd horaires",
                ]
            ]
            .sum()
        )

        ca_chart = (
            alt.Chart(pivot_ca)
            .mark_line(point=True)
            .encode(
                x="Date:T",
                y=alt.Y("Chiffre d’affaires (€):Q", title="CA (€)"),
                color="Période de close:N",
                tooltip=[
                    "Date:T",
                    "Ville:N",
                    "Période de close:N",
                    "Chiffre d’affaires (€):Q",
                    "Nombre commandes:Q",
                ],
            )
            .properties(height=350)
        )
        st.altair_chart(ca_chart, use_container_width=True)

        st.markdown("### 📦 Évolution du nombre de commandes par période de close")
        cmd_chart = (
            alt.Chart(pivot_ca)
            .mark_line(point=True)
            .encode(
                x="Date:T",
                y=alt.Y("Nombre commandes:Q", title="Nombre de commandes"),
                color="Période de close:N",
                tooltip=[
                    "Date:T",
                    "Ville:N",
                    "Période de close:N",
                    "Nombre commandes:Q",
                ],
            )
            .properties(height=350)
        )
        st.altair_chart(cmd_chart, use_container_width=True)

        st.markdown("### 🔥 Heatmap CA horaire (Date × Période de close)")
        heat = df_ca_f.copy()
        heat["Date_str"] = heat["Date"].dt.strftime("%Y-%m-%d")

        heat_chart = (
            alt.Chart(heat)
            .mark_rect()
            .encode(
                x=alt.X("Période de close:N", title="Période de close"),
                y=alt.Y("Date_str:O", title="Date"),
                color=alt.Color("CA horaire (€ / h):Q", title="CA horaire (€ / h)"),
                tooltip=[
                    "Date:T",
                    "Ville:N",
                    "Période de close:N",
                    "CA horaire (€ / h):Q",
                    "Chiffre d’affaires (€):Q",
                    "Nombre commandes:Q",
                ],
            )
            .properties(height=350)
        )
        st.altair_chart(heat_chart, use_container_width=True)

        st.markdown("### 📊 Détail des données (avec CA horaire & statut objectif)")

        if objectif_ca is not None:
            df_ca_show = df_ca_f.copy()
            df_ca_show["Statut objectif CA"] = np.where(
                df_ca_show["OK_objectif_CA"], "🟢 OK", "🔴 Sous objectif"
            )
        else:
            df_ca_show = df_ca_f.copy()

        st.dataframe(
            df_ca_show.sort_values(["Date", "Ville", "Période de close"]),
            use_container_width=True,
        )

        # PDF report
        st.markdown("### 🧾 Export PDF synthèse")
        if st.button("Générer un PDF de synthèse"):
            pdf_bytes = build_pdf_report(
                df_ca_f, df_notes_f, ville_sel, pd.to_datetime(date_deb), pd.to_datetime(date_fin)
            )
            st.download_button(
                label="📥 Télécharger le PDF",
                data=pdf_bytes,
                file_name=f"rapport_closes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
            )

    # --------- PAGE NOTES / MARQUES ---------
    else:
        st.title("⭐ Évolution des notes – par marque & plateforme")

        if df_notes_f.empty:
            st.warning("Aucune donnée pour les filtres sélectionnés.")
            st.stop()

        marques = ["Toutes"] + sorted(df_notes_f["Marque"].dropna().unique().tolist())
        marque_sel = st.selectbox("Marque", marques)

        df_notes_m = df_notes_f.copy()
        if marque_sel != "Toutes":
            df_notes_m = df_notes_m[df_notes_m["Marque"] == marque_sel]

        moy_uber = df_notes_m["Note Uber Eats"].mean()
        moy_deliv = df_notes_m["Note Deliveroo"].mean()

        col1, col2 = st.columns(2)
        col1.metric("Note moyenne Uber Eats", f"{moy_uber:.2f}")
        col2.metric("Note moyenne Deliveroo", f"{moy_deliv:.2f}")

        # Objectif étoiles
        note_min = objectifs["note_min"]
        df_notes_m["OK_objectif_note"] = (
            (df_notes_m["Note Uber Eats"] >= note_min)
            & (df_notes_m["Note Deliveroo"] >= note_min)
        )
        nb_ok_note = int(df_notes_m["OK_objectif_note"].sum())
        nb_total_note = len(df_notes_m)
        pct_ok_note = 100 * nb_ok_note / nb_total_note if nb_total_note > 0 else 0

        emoji_note = "🟢" if pct_ok_note >= 80 else "🟡" if pct_ok_note >= 50 else "🔴"
        st.markdown(
            f"**Objectif étoiles : {note_min} minimum (Uber & Deliveroo)**  "
            f"→ Lignes ≥ objectif : **{nb_ok_note} / {nb_total_note}** ({pct_ok_note:.1f} %) {emoji_note}"
        )

        st.markdown("### 🏅 Performance par marque (moyenne sur la période)")
        perf_marques = (
            df_notes_f.groupby(["Ville", "Marque"], as_index=False)[
                ["Note Uber Eats", "Note Deliveroo"]
            ]
            .mean(numeric_only=True)
            .sort_values(["Ville", "Marque"])
        )
        st.dataframe(perf_marques, use_container_width=True)

        st.markdown("### 📈 Évolution des notes par marque et plateforme")

        notes_long = df_notes_m.melt(
            id_vars=["Date", "Ville", "Marque"],
            value_vars=["Note Uber Eats", "Note Deliveroo"],
            var_name="Plateforme",
            value_name="Note",
        )

        notes_chart = (
            alt.Chart(notes_long)
            .mark_line(point=True)
            .encode(
                x="Date:T",
                y=alt.Y("Note:Q", scale=alt.Scale(domain=[0, 5])),
                color="Plateforme:N",
                tooltip=[
                    "Date:T",
                    "Ville:N",
                    "Marque:N",
                    "Plateforme:N",
                    "Note:Q",
                ],
            )
            .properties(height=350)
        )

        st.altair_chart(notes_chart, use_container_width=True)

        st.markdown("### 📊 Détail des données (avec statut objectif)")
        df_notes_show = df_notes_m.copy()
        df_notes_show["Statut objectif notes"] = np.where(
            df_notes_show["OK_objectif_note"], "🟢 OK", "🔴 Sous objectif"
        )
        st.dataframe(
            df_notes_show.sort_values(["Date", "Ville", "Marque"]),
            use_container_width=True,
        )

# -------------------- MODE SAISIE DES DONNÉES --------------------

else:
    st.title("📝 Saisie / mise à jour des données")

    st.markdown(
        """
        Utilise ces formulaires pour ajouter des lignes à tes données.
        Ensuite, tu peux **télécharger un Excel mis à jour** et le réutiliser comme source.
        """
    )

    tab1, tab2 = st.tabs(
        ["Ajouter une ligne CA_Close", "Ajouter une ligne Évolution_Notes"]
    )

    # --- Formulaire CA_Close ---
    with tab1:
        st.subheader("Ajouter une ligne de close (CA & commandes)")

        with st.form("form_ca"):
            col1, col2 = st.columns(2)
            date_new = col1.date_input("Date")
            ville_new = col2.selectbox(
                "Ville", sorted(df_ca["Ville"].dropna().unique().tolist())
            )
            periode_new = st.selectbox(
                "Période de close",
                sorted(df_ca["Période de close"].dropna().unique().tolist()),
            )
            col3, col4 = st.columns(2)
            cmd_new = col3.number_input(
                "Nombre de commandes", min_value=0, step=1
            )
            ca_new = col4.number_input(
                "Chiffre d’affaires (€)", min_value=0.0, step=1.0, format="%.2f"
            )

            submitted_ca = st.form_submit_button("Ajouter cette ligne")

        if submitted_ca:
            new_row = {
                "Date": pd.to_datetime(date_new),
                "Ville": ville_new,
                "Nombre commandes": int(cmd_new),
                "Chiffre d’affaires (€)": float(ca_new),
                "Période de close": periode_new,
            }
            df_ca_new = pd.concat([df_ca, pd.DataFrame([new_row])], ignore_index=True)
            df_ca_new = add_ca_horaire(df_ca_new)
            st.session_state["df_ca"] = df_ca_new
            df_ca = df_ca_new
            st.success("✅ Ligne CA_Close ajoutée (mémoire session).")

    # --- Formulaire Évolution_Notes ---
    with tab2:
        st.subheader("Ajouter une ligne de notes (étoiles)")

        with st.form("form_notes"):
            col1, col2 = st.columns(2)
            date_n = col1.date_input("Date", key="date_notes")
            ville_n = col2.selectbox(
                "Ville",
                sorted(df_notes["Ville"].dropna().unique().tolist()),
                key="ville_notes",
            )
            marque_n = st.selectbox(
                "Marque", sorted(df_notes["Marque"].dropna().unique().tolist())
            )
            col3, col4 = st.columns(2)
            note_uber_n = col3.number_input(
                "Note Uber Eats", min_value=0.0, max_value=5.0, step=0.1
            )
            note_deliv_n = col4.number_input(
                "Note Deliveroo", min_value=0.0, max_value=5.0, step=0.1
            )

            submitted_notes = st.form_submit_button("Ajouter cette ligne")

        if submitted_notes:
            new_row_n = {
                "Date": pd.to_datetime(date_n),
                "Ville": ville_n,
                "Marque": marque_n,
                "Note Uber Eats": float(note_uber_n),
                "Note Deliveroo": float(note_deliv_n),
            }
            df_notes_new = pd.concat(
                [df_notes, pd.DataFrame([new_row_n])], ignore_index=True
            )
            st.session_state["df_notes"] = df_notes_new
            df_notes = df_notes_new
            st.success("✅ Ligne Évolution_Notes ajoutée (mémoire session).")

    st.markdown("### 💾 Télécharger les données mises à jour")
    updated_bytes = build_excel_bytes(df_ca, df_notes)
    st.download_button(
        label="📥 Télécharger l'Excel mis à jour",
        data=updated_bytes,
        file_name="suivi_close_amiens_beauvais_updated.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    st.markdown("### 👀 Aperçu rapide des dernières lignes")
    col1, col2 = st.columns(2)
    col1.write("Dernières lignes CA_Close")
    col1.dataframe(
        df_ca.sort_values("Date").tail(10), use_container_width=True
    )
    col2.write("Dernières lignes Évolution_Notes")
    col2.dataframe(
        df_notes.sort_values("Date").tail(10), use_container_width=True
    )
