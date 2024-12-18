import streamlit as st
import pandas as pd
from datetime import datetime
import json
import base64
import plotly.graph_objects as go
from collections import defaultdict

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

# Constantes
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

# Fonctions de sauvegarde et chargement JSON
def save_to_json():
    """Convertit les données en JSON et crée un fichier téléchargeable"""
    json_str = json.dumps(st.session_state.risk_families, ensure_ascii=False, indent=2)
    b64 = base64.b64encode(json_str.encode()).decode()
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"risk_data_{current_time}.json"
    href = f'<a href="data:file/json;base64,{b64}" download="{filename}">Télécharger la sauvegarde</a>'
    return href

def load_from_json(uploaded_file):
    """Charge les données depuis un fichier JSON"""
    try:
        content = uploaded_file.getvalue().decode()
        data = json.loads(content)
        st.session_state.risk_families = data
        st.success("Données chargées avec succès !")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur lors du chargement : {str(e)}")

# Fonctions de gestion des données
def add_risk(family_key, risk_name, description, processes=None):
    """Ajoute un nouveau risque"""
    if not risk_name:
        return
    risk_key = f"{family_key} - {risk_name}"
    st.session_state.risk_families[family_key]["risks"][risk_key] = {
        "description": description,
        "processes": processes or [],
        "measures": {k: [] for k in MEASURE_TYPES}
    }

def add_measure(family_key, risk_key, measure_type, measure):
    """Ajoute une nouvelle mesure à un risque"""
    if not measure:
        return
    st.session_state.risk_families[family_key]["risks"][risk_key]["measures"][measure_type].append(measure)

def delete_risk(family_key, risk_key):
    """Supprime un risque"""
    if risk_key in st.session_state.risk_families[family_key]["risks"]:
        del st.session_state.risk_families[family_key]["risks"][risk_key]

def delete_measure(family_key, risk_key, measure_type, measure_index):
    """Supprime une mesure"""
    measures = st.session_state.risk_families[family_key]["risks"][risk_key]["measures"][measure_type]
    if 0 <= measure_index < len(measures):
        del measures[measure_index]

def get_risk_stats():
    """Calcule les statistiques sur les risques et mesures"""
    stats = {
        "total_risks": 0,
        "total_measures": 0,
        "coverage_by_process": defaultdict(int),
        "measures_by_type": defaultdict(lambda: defaultdict(int))
    }
    
    for family_key, family_data in st.session_state.risk_families.items():
        for risk_key, risk_data in family_data["risks"].items():
            stats["total_risks"] += 1
            
            # Comptage des mesures par type
            for measure_type, measures in risk_data["measures"].items():
                measure_count = len(measures)
                stats["total_measures"] += measure_count
                stats["measures_by_type"][family_key][measure_type] += measure_count
            
            # Comptage des risques par processus
            for process in risk_data.get("processes", []):
                stats["coverage_by_process"][process] += 1
    
    return stats

# Fonctions d'import/export CSV
def import_data(content):
    """Importe les données depuis un CSV"""
    try:
        df = pd.read_csv(content, sep=';')
        for _, row in df.iterrows():
            family = row['family']
            if family in st.session_state.risk_families:
                risk_key = f"{family} - {row['risk']}"
                st.session_state.risk_families[family]["risks"][risk_key] = {
                    "description": row['description'],
                    "processes": row.get('processes', '').split('|') if pd.notna(row.get('processes', '')) else [],
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
    """Exporte les données en CSV"""
    rows = []
    for family_key, family_data in st.session_state.risk_families.items():
        for risk_key, risk_data in family_data["risks"].items():
            row = {
                'family': family_key,
                'risk': risk_key.replace(f"{family_key} - ", ""),
                'description': risk_data['description'],
                'processes': '|'.join(risk_data.get('processes', []))
            }
            for measure_type in MEASURE_TYPES:
                row[f'measures_{measure_type}'] = '|'.join(risk_data['measures'][measure_type])
            rows.append(row)
    
    df = pd.DataFrame(rows)
    return df.to_csv(index=False, sep=';')

# Titre principal
st.title("Gestion des Risques par Processus")

# Barre latérale pour les filtres globaux
with st.sidebar:
    st.header("Filtres")
    selected_process = st.selectbox("Processus", ["Tous"] + PROCESSES)
    selected_measure_type = st.selectbox("Type de Mesure", ["Tous"] + list(MEASURE_TYPES.values()))
    search_term = st.text_input("Recherche")

    # Ajout des statistiques dans la barre latérale
    st.header("Statistiques")
    stats = get_risk_stats()
    st.metric("Total des risques", stats["total_risks"])
    st.metric("Total des mesures", stats["total_measures"])

# Création des onglets de navigation
tab1, tab2, tab3 = st.tabs(["Vue par Risques", "Vue par Processus", "Vue par Service"])

# Section Import/Export des données
st.divider()
st.subheader("Import/Export des données")
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

# Section Sauvegarde/Restauration
st.divider()
st.subheader("Sauvegarde des données")
col3, col4 = st.columns(2)

with col3:
    st.write("Sauvegarder l'état actuel")
    st.markdown(save_to_json(), unsafe_allow_html=True)

with col4:
    st.write("Charger une sauvegarde")
    json_file = st.file_uploader("Fichier de sauvegarde", type=['json'])
    if json_file:
        load_from_json(json_file)
