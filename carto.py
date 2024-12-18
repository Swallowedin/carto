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

# Fonctions pour la gestion des données
def add_risk(family_key, risk_name, description):
    if not risk_name:
        return
    risk_key = f"{family_key} - {risk_name}"
    st.session_state.risk_families[family_key]["risks"][risk_key] = {
        "description": description,
        "measures": {k: [] for k in MEASURE_TYPES}
    }

def add_measure(family_key, risk_key, measure_type, measure):
    if not measure:
        return
    st.session_state.risk_families[family_key]["risks"][risk_key]["measures"][measure_type].append(measure)

def delete_risk(family_key, risk_key):
    if risk_key in st.session_state.risk_families[family_key]["risks"]:
        del st.session_state.risk_families[family_key]["risks"][risk_key]

def delete_measure(family_key, risk_key, measure_type, measure_index):
    measures = st.session_state.risk_families[family_key]["risks"][risk_key]["measures"][measure_type]
    if 0 <= measure_index < len(measures):
        del measures[measure_index]

def import_data(content):
    try:
        df = pd.read_csv(content, sep=';')
        for _, row in df.iterrows():
            family = row['family']
            if family in st.session_state.risk_families:
                risk_key = f"{family} - {row['risk']}"
                st.session_state.risk_families[family]["risks"][risk_key] = {
                    "description": row['description'],
                    "measures": {
                        k: row[f'measures_{k}'].split('|') if pd.notna(row[f'measures_{k}']) else []
                        for k in MEASURE_TYPES
                    }
                }
        return True
    except Exception as e:
        st.error(f"Erreur lors de l'import: {str(e)}")
        return False

def export_data():
    rows = []
    for family_key, family_data in st.session_state.risk_families.items():
        for risk_key, risk_data in family_data["risks"].items():
            row = {
                'family': family_key,
                'risk': risk_key.replace(f"{family_key} - ", ""),
                'description': risk_data['description']
            }
            for measure_type in MEASURE_TYPES:
                row[f'measures_{measure_type}'] = '|'.join(risk_data['measures'][measure_type])
            rows.append(row)
    
    df = pd.DataFrame(rows)
    return df.to_csv(index=False, sep=';')

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
        if import_data(uploaded_file):
            st.success("Import réussi")

with col2:
    if st.button("Exporter les données"):
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
        with st.form(key=f"risk_form_{family_key}"):
            st.subheader("Nouveau Risque")
            risk_name = st.text_input("Nom", key=f"name_{family_key}")
            risk_desc = st.text_area("Description", key=f"desc_{family_key}")
            if st.form_submit_button("Ajouter"):
                add_risk(family_key, risk_name, risk_desc)
                st.success("Risque ajouté")
                st.rerun()

        # Affichage des risques existants
        for risk_key, risk_data in family_data["risks"].items():
            st.markdown(f"### {risk_key}")
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
                with st.form(key=f"measure_form_{risk_key}_{measure_type}"):
                    measure = st.text_input("Nouvelle mesure", key=f"measure_{risk_key}_{measure_type}")
                    if st.form_submit_button("Ajouter"):
                        add_measure(family_key, risk_key, measure_type, measure)
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
