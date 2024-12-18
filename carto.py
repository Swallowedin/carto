import streamlit as st
import pandas as pd
from datetime import datetime

# Configuration de la page
st.set_page_config(page_title="Gestion des Risques", layout="wide")

# Initialisation des données dans la session state
if 'risk_families' not in st.session_state:
    st.session_state.risk_families = {
        "CAD": {"name": "Cadeaux et Invitations", "risks": {}},
        "CON": {"name": "Conflits d'intérêts", "risks": {}},
        "COR": {"name": "Corruption", "risks": {}},
        "FAV": {"name": "Favoritisme", "risks": {}},
        "FRAUD": {"name": "Fraude", "risks": {}},
        "MGMT": {"name": "Management", "risks": {}}
    }

PROCESSES = [
    "DIRECTION", "INTERNATIONAL", "PERFORMANCE", "DEVELOPPEMENT_NATIONAL",
    "DEVELOPPEMENT_INTERNATIONAL", "RSE", "GESTION_RISQUES", "FUSAC",
    "INNOV_TRANSFO", "VENTE", "MAGASIN", "LOGISTIQUE", "APPROVISONNEMENT",
    "ACHATS", "SAV", "IMPORT", "FINANCEMENT", "AUTRES_MODES_VENTE",
    "VALO_DECHETS", "QUALITE", "VENTE WEB", "FRANCHISE", "COMPTABILITE",
    "DSI", "RH", "MARKETING", "ORGANISATION", "TECHNIQUE", "JURIDIQUE", "SECURITE"
]

MEASURE_TYPES = {
    "D": "Détection",
    "R": "Réduction",
    "A": "Acceptation",
    "F": "Refus",
    "T": "Transfert"
}

# Titre de l'application
st.title("Gestion des Risques par Processus")

# Barre latérale
with st.sidebar:
    st.header("Filtres")
    selected_process = st.selectbox("Processus", ["Tous"] + PROCESSES)
    selected_measure_type = st.selectbox("Type de Mesure", ["Tous"] + list(MEASURE_TYPES.values()))
    search_term = st.text_input("Recherche")

# Fonction principale pour ajouter un risque
def add_risk(family_key, risk_name, description):
    if not risk_name:
        return
    risk_key = f"{family_key} - {risk_name}"
    st.session_state.risk_families[family_key]["risks"][risk_key] = {
        "description": description,
        "measures": {k: [] for k in MEASURE_TYPES}
    }

# Fonction pour ajouter une mesure
def add_measure(family_key, risk_key, measure_type, measure):
    if not measure:
        return
    st.session_state.risk_families[family_key]["risks"][risk_key]["measures"][measure_type].append(measure)

# Interface principale
for family_key, family in st.session_state.risk_families.items():
    with st.expander(family["name"]):
        # Formulaire pour nouveau risque
        with st.form(key=f"risk_form_{family_key}"):
            st.subheader("Nouveau Risque")
            risk_name = st.text_input("Nom", key=f"name_{family_key}")
            risk_desc = st.text_area("Description", key=f"desc_{family_key}")
            submit = st.form_submit_button("Ajouter")
            if submit:
                add_risk(family_key, risk_name, risk_desc)
                st.success("Risque ajouté")
                st.rerun()

        # Affichage des risques existants
        for risk_key, risk in family["risks"].items():
            st.markdown(f"### {risk_key}")
            st.write(risk["description"])
            
            # Mesures pour chaque risque
            for measure_type, measure_name in MEASURE_TYPES.items():
                st.markdown(f"**{measure_name}**")
                measures = risk["measures"][measure_type]
                
                # Ajout de nouvelle mesure
                with st.form(key=f"measure_form_{risk_key}_{measure_type}"):
                    measure = st.text_input("Nouvelle mesure", key=f"measure_{risk_key}_{measure_type}")
                    if st.form_submit_button("Ajouter"):
                        add_measure(family_key, risk_key, measure_type, measure)
                        st.rerun()
                
                # Liste des mesures existantes
                for m in measures:
                    st.write(f"- {m}")

# Interface utilisateur
st.title("Gestion des Risques par Processus")

# Barre latérale pour les filtres
with st.sidebar:
    st.header("Filtres")
    selected_process = st.selectbox("Processus", ["Tous"] + PROCESSES)
    selected_measure_type = st.selectbox("Type de Mesure", ["Tous"] + list(MEASURE_TYPES.values()))
    search_term = st.text_input("Recherche")

# Import/Export
col1, col2 = st.columns(2)
with col1:
    uploaded_file = st.file_uploader("Importer des données (CSV)", type="csv")
    if uploaded_file:
        content = uploaded_file.getvalue().decode()
        if import_data(content):
            st.success("Import réussi")

with col2:
    if st.button("Exporter les données (CSV)"):
        csv_data = export_data()
        st.download_button(
            label="Télécharger CSV",
            data=csv_data,
            file_name=f"gestion_risques_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )

# Affichage principal
for family_key, family_data in st.session_state.risk_families.items():
    with st.expander(f"{family_data['name']}", expanded=True):
        # Ajout d'un nouveau risque
        if st.button(f"Nouveau Risque", key=f"new_risk_{family_key}"):
            with st.form(f"new_risk_form_{family_key}"):
                risk_name = st.text_input("Nom du risque")
                risk_description = st.text_area("Description")
                if st.form_submit_button("Ajouter"):
                    add_risk(family_key, risk_name, risk_description)
                    st.success("Risque ajouté avec succès")
                    st.rerun()

        # Affichage des risques existants
        for risk_key, risk_data in family_data["risks"].items():
            st.subheader(risk_key)
            st.write(risk_data["description"])
            
            col1, col2 = st.columns([10, 1])
            with col2:
                if st.button("🗑️", key=f"delete_{risk_key}"):
                    delete_risk(family_key, risk_key)
                    st.rerun()

            # Mesures
            for measure_type, measures in risk_data["measures"].items():
                st.write(f"**{MEASURE_TYPES[measure_type]}**")
                
                # Ajout d'une nouvelle mesure
                new_measure = st.text_input("Nouvelle mesure", key=f"new_measure_{risk_key}_{measure_type}")
                if st.button("Ajouter", key=f"add_measure_{risk_key}_{measure_type}"):
                    add_measure(family_key, risk_key, measure_type, new_measure)
                    st.rerun()

                # Liste des mesures existantes
                for i, measure in enumerate(measures):
                    col1, col2 = st.columns([10, 1])
                    with col1:
                        st.write(f"- {measure}")
                    with col2:
                        if st.button("🗑️", key=f"delete_measure_{risk_key}_{measure_type}_{i}"):
                            delete_measure(family_key, risk_key, measure_type, i)
                            st.rerun()

            # Mesures
            for measure_type, measures in risk_data["measures"].items():
                st.write(f"**{MEASURE_TYPES[measure_type]}**")
                
                # Ajout d'une nouvelle mesure
                new_measure = st.text_input("Nouvelle mesure", key=f"new_measure_{risk_key}_{measure_type}")
                if st.button("Ajouter", key=f"add_measure_{risk_key}_{measure_type}"):
                    add_measure(family_key, risk_key, measure_type, new_measure)
                    st.rerun()

                # Liste des mesures existantes
                for i, measure in enumerate(measures):
                    col1, col2 = st.columns([10, 1])
                    with col1:
                        st.write(f"- {measure}")
                    with col2:
                        if st.button("🗑️", key=f"delete_measure_{risk_key}_{measure_type}_{i}"):
                            delete_measure(family_key, risk_key, measure_type, i)
                            st.rerun()

if __name__ == '__main__':
    st.run()
