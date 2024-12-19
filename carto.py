import streamlit as st
import pandas as pd
from datetime import datetime
import json
import base64
import plotly.graph_objects as go
from collections import defaultdict

# Configuration de la page
st.set_page_config(
    page_title="Gestion des Risques",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Style CSS simplifié
st.markdown("""
    <style>
    .block-container {padding: 1rem;}
    .element-container {margin-bottom: 0.5rem;}
    .risk-family-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem;
    }
    .compact-button {padding: 0.25rem !important;}
    .stButton>button {
        padding: 0.25rem 0.5rem;
        font-size: 0.8rem;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 0.9rem;
        margin-bottom: 0rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialisation session state
if 'risk_families' not in st.session_state:
    st.session_state.risk_families = {}

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

# Fonctions de base
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

def add_risk_family(family_key, family_name):
    """Ajoute une nouvelle famille de risques"""
    if family_key and family_name:
        st.session_state.risk_families[family_key] = {
            "name": family_name,
            "risks": {}
        }

def add_risk(family_key, risk_name, description, processes=None):
    """Ajoute un nouveau risque à une famille"""
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
    if measure:
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

# Interface principale
header_col1, header_col2, header_col3 = st.columns([2, 1, 1])
with header_col1:
    st.header("Gestion des Risques")
with header_col2:
    uploaded_file = st.file_uploader("Import CSV", type="csv", label_visibility="collapsed")
    if uploaded_file and import_data(uploaded_file):
        st.success("Import réussi")
with header_col3:
    if st.button("➕ Nouvelle Famille", use_container_width=True):
        st.session_state.show_family_form = True

# Formulaire d'ajout de famille
if st.session_state.get('show_family_form', False):
    with st.form("new_family_form"):
        st.subheader("Nouvelle Famille de Risques")
        col1, col2 = st.columns(2)
        with col1:
            family_key = st.text_input("Code", placeholder="Ex: FIN")
        with col2:
            family_name = st.text_input("Nom", placeholder="Ex: Finance")
        
        col3, col4 = st.columns(2)
        with col3:
            if st.form_submit_button("Ajouter"):
                if family_key and family_name:
                    add_risk_family(family_key, family_name)
                    st.session_state.show_family_form = False
                    st.rerun()
        with col4:
            if st.form_submit_button("Annuler"):
                st.session_state.show_family_form = False
                st.rerun()

# Onglets principaux
tab1, tab2, tab3 = st.tabs([
    "📊 Risques | Gestion par famille",
    "🔄 Processus | Vue par processus",
    "🏢 Service | Impact par service"
])

# Tab 1: Gestion par famille
with tab1:
    # Barre de recherche et filtres
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("🔍", placeholder="Rechercher...")
    with col2:
        selected_process = st.selectbox("Processus", ["Tous"] + PROCESSES)
    with col3:
        selected_measure_type = st.selectbox("Type de mesure", ["Tous"] + list(MEASURE_TYPES.values()))

    # Affichage des familles de risques
    for family_key, family_data in st.session_state.risk_families.items():
        with st.expander(f"📁 {family_data['name']}", expanded=False):
            # En-tête compact
            col1, col2 = st.columns([5, 1])
            with col2:
                if st.button("➕", key=f"add_risk_{family_key}", help="Ajouter un risque"):
                    st.session_state[f"show_risk_form_{family_key}"] = True

            # Formulaire d'ajout de risque
            if st.session_state.get(f"show_risk_form_{family_key}", False):
                with st.form(key=f"risk_form_{family_key}"):
                    risk_name = st.text_input("Nom du risque", key=f"risk_name_{family_key}")
                    risk_desc = st.text_area("Description", key=f"risk_desc_{family_key}", height=100)
                    selected_processes = st.multiselect("Processus concernés", PROCESSES)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("Ajouter"):
                            add_risk(family_key, risk_name, risk_desc, selected_processes)
                            st.session_state[f"show_risk_form_{family_key}"] = False
                            st.rerun()
                    with col2:
                        if st.form_submit_button("Annuler"):
                            st.session_state[f"show_risk_form_{family_key}"] = False
                            st.rerun()

            # Liste des risques
            for risk_key, risk_data in family_data["risks"].items():
                # Filtrage
                if selected_process != "Tous" and selected_process not in risk_data.get("processes", []):
                    continue
                if search_term and search_term.lower() not in risk_key.lower():
                    continue

                with st.container():
                    # En-tête du risque
                    cols = st.columns([6, 1, 1])
                    with cols[0]:
                        st.markdown(f"**{risk_key.split(' - ')[1]}**")
                        st.caption(risk_data["description"])
                    with cols[1]:
                        if st.button("📝", key=f"edit_{risk_key}"):
                            st.session_state[f"edit_risk_{risk_key}"] = True
                    with cols[2]:
                        if st.button("🗑️", key=f"del_{risk_key}"):
                            delete_risk(family_key, risk_key)
                            st.rerun()

                    # Modification de la gestion des mesures pour un risque
                    with st.expander("Ajouter une mesure", expanded=False):
                        with st.form(key=f"measure_form_{risk_key}"):
                            new_measure = st.text_area(
                                "Description de la mesure",
                                key=f"measure_desc_{risk_key}",
                                placeholder="Décrivez la mesure...",
                                height=100
                            )
                            
                            # Cases à cocher pour les types de mesure
                            st.write("Type de mesure :")
                            cols = st.columns(5)
                            measure_types_selected = {}
                            for i, (m_type, m_name) in enumerate(MEASURE_TYPES.items()):
                                with cols[i]:
                                    measure_types_selected[m_type] = st.checkbox(
                                        m_name,
                                        key=f"measure_type_{risk_key}_{m_type}"
                                    )
                            
                            if st.form_submit_button("Ajouter la mesure"):
                                if new_measure:
                                    for m_type, selected in measure_types_selected.items():
                                        if selected:
                                            add_measure(family_key, risk_key, m_type, new_measure)
                                    st.success("Mesure ajoutée")
                                    st.rerun()
                    
                    # Affichage des mesures existantes
                    if any(risk_data["measures"].values()):
                        with st.expander("Mesures existantes", expanded=True):
                            # Création d'un dictionnaire inversé pour regrouper les mesures identiques
                            measures_by_description = defaultdict(list)
                            for m_type, measures in risk_data["measures"].items():
                                for measure in measures:
                                    measures_by_description[measure].append(m_type)
                            
                            # Affichage des mesures avec leurs types
                            for measure, types in measures_by_description.items():
                                col1, col2 = st.columns([5, 1])
                                with col1:
                                    st.write(f"📝 {measure}")
                                    st.caption(f"Types : {', '.join([MEASURE_TYPES[t] for t in types])}")
                                with col2:
                                    if st.button("🗑️", key=f"del_measure_{risk_key}_{hash(measure)}"):
                                        # Suppression de la mesure de tous les types associés
                                        for m_type in types:
                                            measures = risk_data["measures"][m_type]
                                            if measure in measures:
                                                measures.remove(measure)
                                        st.rerun()					

with tab2:
    st.header("Vue par Processus")
    
    selected_process_view = st.selectbox(
        "Sélectionner un processus",
        PROCESSES,
        key="process_view_selector"
    )
    
    # Statistiques du processus
    process_stats = get_process_coverage_stats(selected_process_view)
    
    # Métriques clés
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Risques identifiés", process_stats["total_risks"])
    with col2:
        st.metric("Mesures en place", process_stats["total_measures"])
    with col3:
        coverage_pct = (process_stats["total_measures"] / (process_stats["total_risks"] * 5)) * 100 if process_stats["total_risks"] > 0 else 0
        st.metric("Taux de couverture", f"{coverage_pct:.1f}%")
    
    # Répartition des mesures par type
    st.subheader("Répartition des mesures")
    measure_cols = st.columns(len(MEASURE_TYPES))
    for i, (measure_type, measure_name) in enumerate(MEASURE_TYPES.items()):
        with measure_cols[i]:
            st.metric(
                measure_name,
                process_stats["measures_by_type"][measure_type]
            )
    
    # Liste des risques associés
    st.subheader("Risques associés")
    process_risks = get_risks_by_process(selected_process_view)
    
    if process_risks:
        for risk in process_risks:
            with st.expander(f"{risk['risk']}", expanded=False):
                st.write(risk["description"])
                
                # Affichage des mesures
                for measure_type, measures in risk["measures"].items():
                    if measures:
                        st.write(f"**{MEASURE_TYPES[measure_type]}**")
                        for measure in measures:
                            st.write(f"- {measure}")
    else:
        st.info("Aucun risque associé à ce processus")

# Tab 3: Vue par service
with tab3:
    st.header("Vue par Service")
    
    selected_service = st.selectbox(
        "Sélectionner un service",
        PROCESSES,
        key="service_view_selector"
    )
    
    # Création de la matrice de risques
    risk_matrix = defaultdict(lambda: defaultdict(list))
    for family_key, family_data in st.session_state.risk_families.items():
        for risk_key, risk_data in family_data["risks"].items():
            if selected_service in risk_data.get("processes", []):
                risk_matrix[family_key].append({
                    "risk_key": risk_key,
                    "description": risk_data["description"],
                    "measures": risk_data["measures"],
                    "measure_count": sum(len(m) for m in risk_data["measures"].values())
                })
    
    if risk_matrix:
        # Statistiques du service
        total_risks = sum(len(risks) for risks in risk_matrix.values())
        total_measures = sum(
            sum(risk["measure_count"] for risk in risks)
            for risks in risk_matrix.values()
        )
        
        # Métriques du service
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total des risques", total_risks)
        with col2:
            st.metric("Total des mesures", total_measures)
        
        # Affichage par famille
        for family_key, risks in risk_matrix.items():
            with st.expander(f"{family_key} ({len(risks)} risques)", expanded=True):
                for risk in risks:
                    st.markdown(f"### {risk['risk_key']}")
                    st.write(risk["description"])
                    
                    measures_summary = []
                    for m_type, measures in risk["measures"].items():
                        if measures:
                            measures_summary.append(f"**{MEASURE_TYPES[m_type]}**: {len(measures)}")
                    st.markdown(" | ".join(measures_summary))
    else:
        st.info("Aucun risque associé à ce service")

# Configuration des styles finaux
st.markdown("""
    <style>
    .metric-container {
        padding: 0.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: bold;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #6c757d;
    }
    </style>
""", unsafe_allow_html=True)

# Configuration des notifications
if "notifications" not in st.session_state:
    st.session_state.notifications = []

# Gestion des notifications
for notification in st.session_state.notifications:
    st.toast(notification["message"])
st.session_state.notifications = []
