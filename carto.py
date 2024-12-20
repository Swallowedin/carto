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
    initial_sidebar_state="collapsed",
    menu_items=None
)

st.markdown("""
   <style>
   /* Cacher la barre Streamlit */
   #MainMenu {visibility: hidden;}
   footer {visibility: hidden;}
   header {visibility: hidden;}

   /* Style de base de la page - Plus compact */
   .block-container {
       padding: 0.5rem 0.5rem 5rem !important;
       max-width: 100% !important;
   }
   
   /* Réduction des espacements */
   div[data-testid="stVerticalBlock"] > div {
       padding: 0.2rem 0 !important;
   }

   /* Style plus austère pour les expansions */
   .streamlit-expanderHeader {
       font-size: 0.9rem !important;
       padding: 0.3rem !important;
       background: #fafafa !important;
       border: none !important;
   }

   /* Style de l'uploader plus compact */
   [data-testid="stFileUploader"] {
       background-color: transparent !important;
       border: 1px solid #eee !important;
       padding: 0.2rem 0.3rem !important;
       border-radius: 3px !important;
       min-height: unset !important;
   }
   
   [data-testid="stFileUploader"]:hover {
       border-color: #ddd !important;
   }

   /* Masquer texte drag and drop */
   [data-testid="stFileUploader"] div {
       display: none !important;
   }

   /* Garder icône et bouton browse */
   [data-testid="stFileUploader"] section {
       display: flex;
       gap: 0.3rem;
       align-items: center;
   }
   
   /* Style compact des boutons de téléchargement */
   .download-link {
       text-decoration: none !important;
       color: #666 !important;
       font-size: 13px !important;
       border: 1px solid #eee !important;
       padding: 0.2rem 0.4rem !important;
       border-radius: 3px !important;
   }

   .download-link:hover {
       border-color: #ddd !important;
   }

   .download-container {
       display: flex;
       gap: 0.3rem;
       align-items: center;
       padding-top: 0.1rem;
   }

   /* Réduction des marges titres */
   h3 {
       margin: 0 !important;
       padding: 0 !important;
       font-size: 1rem !important;
   }

   /* Style compact des onglets */
   .stTabs [data-baseweb="tab-list"] {
       gap: 1rem;
       margin-top: 0.5rem;
   }

   .stTabs [data-baseweb="tab"] {
       padding: 0.2rem 0.5rem !important;
       font-size: 0.9rem !important;
   }

   /* Style minimaliste du bouton d'ajout */
   [data-testid="baseButton-secondary"] {
       background: transparent !important;
       border: none !important;
       color: #666 !important;
       font-size: 14px !important;
       padding: 0 !important;
       margin: 0 !important;
   }

   /* Réduction taille des inputs */
   .stTextInput input, .stTextArea textarea {
       padding: 0.3rem !important;
       font-size: 0.9rem !important;
   }
   
   /* Style compact des checkboxes */
   .stCheckbox {
       padding: 0.1rem !important;
       margin: 0 !important;
   }
   .stCheckbox label {
       font-size: 0.85rem !important;
   }
   
   /* Réduction marges boutons */
   .stButton {
       margin: 0.1rem 0 !important;
   }
   .stButton button {
       padding: 0.2rem 0.5rem !important;
       font-size: 0.85rem !important;
   }
   
   /* Style compact select boxes */
   .stSelectbox {
       margin: 0.1rem 0 !important;
   }
   .stSelectbox > div > div {
       padding: 0.2rem !important;
   }
   
   /* Réduction marges colonnes */
   .row-widget {
       margin: 0.1rem 0 !important;
   }

   /* Métriques compactes */
   .metric-container {
       padding: 0.3rem;
       border-radius: 0.25rem;
       background-color: #f8f9fa;
       margin: 0.2rem 0;
   }
   .metric-value {
       font-size: 1.1rem;
       font-weight: bold;
   }
   .metric-label {
       font-size: 0.75rem;
       color: #6c757d;
   }
   </style>
""", unsafe_allow_html=True)

# Initialisation session state
if 'risk_families' not in st.session_state:
    st.session_state.risk_families = {}
if 'actions' not in st.session_state:
    st.session_state.actions = {}
if 'measure_status' not in st.session_state:
    st.session_state.measure_status = {}
if 'measure_performance' not in st.session_state:
    st.session_state.measure_performance = {}

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

MEASURE_STATUS = [
    "Non évalué",
    "Efficace",
    "Partiellement efficace",
    "Insuffisant",
    "Critique"
]

ACTION_STATUS = [
    "À faire",
    "En cours",
    "En attente",
    "Terminé",
    "Annulé"
]

ACTION_PRIORITY = [
    "BASSE",
    "NORMALE",
    "HAUTE",
    "CRITIQUE"
]

# Couleurs pour les différents statuts
STATUS_COLORS = {
    "Non évalué": "#6c757d",
    "Efficace": "#28a745",
    "Partiellement efficace": "#ffc107",
    "Insuffisant": "#dc3545",
    "Critique": "#dc3545",
    "À faire": "#6c757d",
    "En cours": "#17a2b8",
    "En attente": "#ffc107",
    "Terminé": "#28a745",
    "Annulé": "#6c757d",
    "BASSE": "#28a745",
    "NORMALE": "#17a2b8",
    "HAUTE": "#ffc107",
    "CRITIQUE": "#dc3545"
}


# Fonctions de gestion des fichiers
def save_to_json():
    """Exporte les données en JSON"""
    json_str = json.dumps(st.session_state.risk_families, ensure_ascii=False, indent=2)
    b64 = base64.b64encode(json_str.encode()).decode()
    current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"risk_data_{current_time}.json"
    return f'<a class="download-link" href="data:file/json;base64,{b64}" download="{filename}">⬇️ JSON</a>'

def save_to_csv():
    """Exporte les données en CSV"""
    rows = []
    for family_key, family_data in st.session_state.risk_families.items():
        for risk_key, risk_data in family_data["risks"].items():
            for measure_type, measures in risk_data["measures"].items():
                for measure in measures:
                    rows.append({
                        "family": family_key,
                        "family_name": family_data["name"],
                        "risk_name": risk_key.split(" - ")[1],
                        "description": risk_data["description"],
                        "processes": "|".join(risk_data["processes"]),
                        "measure_type": measure_type,
                        "measure": measure
                    })
    
    if rows:
        df = pd.DataFrame(rows)
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"risk_data_{current_time}.csv"
        return f'<a class="download-link" href="data:file/csv;base64,{b64}" download="{filename}">⬇️ CSV</a>'
    return ""

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

def load_from_csv(uploaded_file):
    """Charge les données depuis un fichier CSV"""
    try:
        df = pd.read_csv(uploaded_file)
        new_data = {}
        
        # Conversion du CSV en structure de données
        for _, row in df.iterrows():
            family_key = row["family"]
            if family_key not in new_data:
                new_data[family_key] = {
                    "name": row["family_name"],
                    "risks": {}
                }
            
            risk_key = f"{family_key} - {row['risk_name']}"
            if risk_key not in new_data[family_key]["risks"]:
                new_data[family_key]["risks"][risk_key] = {
                    "description": row["description"],
                    "processes": row["processes"].split("|"),
                    "measures": {k: [] for k in MEASURE_TYPES}
                }
            
            new_data[family_key]["risks"][risk_key]["measures"][row["measure_type"]].append(row["measure"])
        
        st.session_state.risk_families = new_data
        st.success("Données chargées avec succès !")
        st.rerun()
    except Exception as e:
        st.error(f"Erreur lors du chargement : {str(e)}")

# Fonctions de gestion des données
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

def add_measure(family_key, risk_key, measure_type, measure_text):
    """Ajoute une ou plusieurs mesures à un risque"""
    if measure_text:
        # Sépare le texte en mesures individuelles basées sur les sauts de ligne
        measures = [m.strip() for m in measure_text.split('\n') if m.strip()]
        for measure in measures:
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

# Fonctions pour les mesures et actions
def get_all_measures():
    """Récupère toutes les mesures avec leur contexte"""
    measures_data = []
    for family_key, family_data in st.session_state.risk_families.items():
        for risk_key, risk_data in family_data["risks"].items():
            risk_name = risk_key.split(" - ")[1]
            for measure_type, measures in risk_data["measures"].items():
                for measure in measures:
                    measure_id = f"{family_key}-{risk_name}-{measure_type}"
                    measures_data.append({
                        "id": measure_id,
                        "famille": family_data["name"],
                        "risque": risk_name,
                        "processus": ", ".join(risk_data["processes"]),
                        "type": MEASURE_TYPES[measure_type],
                        "mesure": measure,
                        "statut": st.session_state.measure_status.get(measure_id, "Non évalué"),
                        "performance": st.session_state.measure_performance.get(measure_id, "N/A")
                    })
    return pd.DataFrame(measures_data)

def get_all_actions():
    """Récupère toutes les actions avec leur contexte"""
    actions_data = []
    for action_id, action in st.session_state.actions.items():
        actions_data.append({
            "id": action_id,
            "mesure_id": action["measure_id"],
            "description": action["description"],
            "responsable": action["responsable"],
            "deadline": action["deadline"],
            "statut": action["statut"],
            "priorite": action["priorite"],
            "commentaire": action["commentaire"]
        })
    return pd.DataFrame(actions_data)

def add_action(measure_id, description, responsable, deadline, priorite="NORMALE"):
    """Ajoute une nouvelle action"""
    action_id = f"action_{len(st.session_state.actions) + 1}"
    st.session_state.actions[action_id] = {
        "measure_id": measure_id,
        "description": description,
        "responsable": responsable,
        "deadline": deadline,
        "statut": "À faire",
        "priorite": priorite,
        "commentaire": ""
    }

def update_action(action_id, **kwargs):
    """Met à jour une action existante"""
    if action_id in st.session_state.actions:
        st.session_state.actions[action_id].update(kwargs)

def update_measure_status(measure_id, status, performance):
    """Met à jour le statut et la performance d'une mesure"""
    st.session_state.measure_status[measure_id] = status
    st.session_state.measure_performance[measure_id] = performance

def delete_action(action_id):
    """Supprime une action"""
    if action_id in st.session_state.actions:
        del st.session_state.actions[action_id]

def get_measures_by_process(process):
    """Filtre les mesures par processus"""
    all_measures = get_all_measures()
    if process != "Tous":
        return all_measures[all_measures["processus"].str.contains(process, na=False)]
    return all_measures
def get_process_coverage_stats(process_name):
    """Calcule les statistiques de couverture pour un processus"""
    stats = {
        "total_risks": 0,
        "measures_by_type": defaultdict(int),
        "risks_by_family": defaultdict(int),
        "total_measures": 0
    }
    
    for family_key, family_data in st.session_state.risk_families.items():
        for risk_key, risk_data in family_data["risks"].items():
            if process_name in risk_data.get("processes", []):
                stats["total_risks"] += 1
                stats["risks_by_family"][family_key] += 1
                
                for measure_type, measures in risk_data["measures"].items():
                    measure_count = len(measures)
                    stats["measures_by_type"][measure_type] += measure_count
                    stats["total_measures"] += measure_count
    
    return stats

def get_risks_by_process(process_name):
    """Récupère tous les risques associés à un processus"""
    process_risks = []
    for family_key, family_data in st.session_state.risk_families.items():
        for risk_key, risk_data in family_data["risks"].items():
            if process_name in risk_data.get("processes", []):
                process_risks.append({
                    "family": family_key,
                    "risk": risk_key,
                    "description": risk_data["description"],
                    "measures": risk_data["measures"]
                })
    return process_risks

# Tab 4: Mesures & Actions
with tab4:
    # Filtres en haut de page
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        view_mode = st.radio("Mode d'affichage", 
                          ["Tableau de bord", "Suivi des mesures", "Actions à suivre"], 
                          horizontal=True)
    with col2:
        filter_process = st.selectbox("Processus", ["Tous"] + PROCESSES)
    with col3:
        filter_measure = st.selectbox("Type", ["Tous"] + list(MEASURE_TYPES.values()))
    with col4:
        filter_status = st.selectbox("Statut", ["Tous"] + MEASURE_STATUS)

    # Récupération des données
    df_measures = get_measures_by_process(filter_process)
    df_actions = get_all_actions()

    # Application des filtres
    if filter_measure != "Tous":
        df_measures = df_measures[df_measures["type"] == filter_measure]
    if filter_status != "Tous":
        df_measures = df_measures[df_measures["statut"] == filter_status]

    if view_mode == "Tableau de bord":
        # Métriques globales
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_measures = len(df_measures)
            st.metric("Mesures", total_measures)
        with col2:
            measures_evaluated = df_measures[df_measures["statut"] != "Non évalué"]
            st.metric("Évaluées", f"{len(measures_evaluated)} ({len(measures_evaluated)/total_measures*100:.0f}%)")
        with col3:
            measures_effective = df_measures[df_measures["statut"] == "Efficace"]
            st.metric("Efficaces", f"{len(measures_effective)} ({len(measures_effective)/total_measures*100:.0f}%)")
        with col4:
            actions_in_progress = len(df_actions[df_actions["statut"].isin(["À faire", "En cours"])])
            st.metric("Actions en cours", actions_in_progress)

        # Graphiques et statistiques
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Statut des mesures")
            status_counts = df_measures["statut"].value_counts()
            st.bar_chart(status_counts)
        with col2:
            st.subheader("Actions par priorité")
            priority_counts = df_actions["priorite"].value_counts()
            st.bar_chart(priority_counts)

    elif view_mode == "Suivi des mesures":
        # Tableau des mesures avec évaluation
        for idx, measure in df_measures.iterrows():
            with st.expander(f"{measure['famille']} - {measure['risque']}", expanded=False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write("**Mesure:**", measure['mesure'])
                    st.write("**Processus:**", measure['processus'])
                    st.write("**Type:**", measure['type'])
                with col2:
                    new_status = st.selectbox(
                        "Statut",
                        MEASURE_STATUS,
                        index=MEASURE_STATUS.index(measure['statut']),
                        key=f"status_{measure['id']}"
                    )
                    new_performance = st.text_area(
                        "Évaluation",
                        value=measure['performance'],
                        key=f"perf_{measure['id']}"
                    )
                    if st.button("Mettre à jour", key=f"update_{measure['id']}"):
                        update_measure_status(measure['id'], new_status, new_performance)
                        st.rerun()

                # Afficher les actions liées
                actions = df_actions[df_actions["mesure_id"] == measure["id"]]
                if len(actions) > 0:
                    st.write("**Actions associées:**")
                    for _, action in actions.iterrows():
                        st.markdown(
                            f"* {action['description']} - "
                            f"*{action['responsable']}* - "
                            f"📅 {action['deadline']} - "
                            f"_{action['statut']}_"
                        )

                # Ajouter une nouvelle action
                if st.button("+ Nouvelle action", key=f"new_action_{measure['id']}"):
                    st.session_state[f"show_action_form_{measure['id']}"] = True

                if st.session_state.get(f"show_action_form_{measure['id']}", False):
                    with st.form(f"action_form_{measure['id']}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            action_desc = st.text_area("Description")
                            action_resp = st.text_input("Responsable")
                        with col2:
                            action_deadline = st.date_input("Échéance")
                            action_priority = st.selectbox("Priorité", ACTION_PRIORITY)
                        
                        submit_col1, submit_col2 = st.columns([1, 4])
                        with submit_col1:
                            if st.form_submit_button("Ajouter"):
                                add_action(measure['id'], action_desc, action_resp, 
                                         action_deadline, action_priority)
                                st.session_state[f"show_action_form_{measure['id']}"] = False
                                st.rerun()
                        with submit_col2:
                            if st.form_submit_button("Annuler"):
                                st.session_state[f"show_action_form_{measure['id']}"] =

# Interface principale
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown("### Gestion des Risques")
with col2:
    upload_col, export_col = st.columns([1, 1])
    with upload_col:
        uploaded_file = st.file_uploader(
            "⬆️ Import",
            type=["json", "csv"], 
            label_visibility="collapsed"
        )
        if uploaded_file:
            if uploaded_file.type == "application/json":
                load_from_json(uploaded_file)
            else:
                load_from_csv(uploaded_file)
    with export_col:
        st.markdown(
            f"""<div class="download-container">{save_to_json()} {save_to_csv()}</div>""", 
            unsafe_allow_html=True
        )

# Onglets principaux
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Risques | Gestion par famille",
    "🔄 Processus | Vue par processus",
    "🏢 Service | Impact par service",
    "🔍 Mesures & Actions"
])

# Tab 1: Gestion des risques par famille
with tab1:
    if st.button("+ Nouvelle Famille", use_container_width=False, type="secondary"):
        st.session_state.show_family_form = True
    
    # Formulaire d'ajout de famille
    if st.session_state.get('show_family_form', False):
        with st.form("new_family_form"):
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
            # Bouton d'ajout de risque
            cols = st.columns([20, 1])
            with cols[1]:
                if st.button("＋", key=f"add_risk_{family_key}", help="Ajouter un risque", type="secondary"):
                    st.session_state[f"show_risk_form_{family_key}"] = True
            
            # Formulaire d'ajout/édition de risque
            if st.session_state.get(f"show_risk_form_{family_key}", False):
                col1, col2 = st.columns([2, 1])
                with col1:
                    risk_name = st.text_input("Nom", key=f"risk_name_{family_key}")
                    risk_desc = st.text_area("Description", key=f"risk_desc_{family_key}", height=80)
                with col2:
                    selected_processes = st.multiselect("Processus", PROCESSES)
                
                # Section des mesures
                st.markdown('<span style="color: #666; font-size: 0.85rem;">Mesures</span>', unsafe_allow_html=True)
                measure_text = st.text_area(
                    "Description",
                    height=80,
                    key=f"measure_text_{family_key}",
                    help="Saisissez une mesure par ligne pour en ajouter plusieurs à la fois",
                    placeholder="Une mesure par ligne..."
                )
                measure_cols = st.columns([3, 3, 3, 3, 3, 1])
                
                # Sélection des types de mesures
                measure_types_selected = {}
                for i, (m_type, m_name) in enumerate(MEASURE_TYPES.items()):
                    with measure_cols[i]:
                        measure_types_selected[m_type] = st.checkbox(m_name, key=f"measure_type_{family_key}_{m_type}")
                
                with measure_cols[-1]:
                    if st.button("＋", key=f"add_measure_{family_key}"):
                        if measure_text and any(measure_types_selected.values()) and risk_name:
                            risk_key = f"{family_key} - {risk_name}"
                            if risk_key not in st.session_state.risk_families[family_key]["risks"]:
                                add_risk(family_key, risk_name, risk_desc, selected_processes)
                            
                            for m_type, selected in measure_types_selected.items():
                                if selected:
                                    add_measure(family_key, risk_key, m_type, measure_text)
                            st.rerun()
                        elif not risk_name:
                            st.error("Veuillez d'abord saisir un nom de risque")

                # Boutons de validation
                col1, col2 = st.columns([1, 4])
                with col1:
                    if st.button("✓ Valider", key=f"validate_{family_key}"):
                        if risk_name:
                            add_risk(family_key, risk_name, risk_desc, selected_processes)
                            st.session_state[f"show_risk_form_{family_key}"] = False
                            st.rerun()
                with col2:
                    if st.button("Annuler", key=f"cancel_{family_key}"):
                        st.session_state[f"show_risk_form_{family_key}"] = False
                        st.rerun()
            
            # Affichage des risques existants
            for risk_key, risk_data in family_data["risks"].items():
                if (selected_process == "Tous" or selected_process in risk_data.get("processes", [])):
                    measure_counts = {
                        MEASURE_TYPES[m_type]: len(measures) 
                        for m_type, measures in risk_data["measures"].items()
                    }
                    
                    cols = st.columns([8, 4, 4, 1])
                    with cols[0]:
                        st.markdown(f"**{risk_key.split(' - ')[1]}**")
                    with cols[1]:
                        st.markdown(", ".join(risk_data["processes"][:2] + (["..."] if len(risk_data["processes"]) > 2 else [])))
                    with cols[2]:
                        st.markdown(" ".join([
                            f'<span style="background:#f5f5f5;padding:0 0.25rem;border-radius:2px;font-size:0.7rem">{t}:{c}</span>'
                            for t, c in measure_counts.items() if c > 0
                        ]), unsafe_allow_html=True)
                    with cols[3]:
                        if st.button("📝", key=f"edit_{risk_key}"):
                            st.session_state[f"edit_risk_{risk_key}"] = True

# Tab 2: Vue par processus
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
    
    # Répartition des mesures
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
    
    # Matrice des risques
    risk_matrix = defaultdict(list)
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
        total_risks = sum(len(risks) for risks in risk_matrix.values())
        total_measures = sum(
            sum(risk["measure_count"] for risk in risks)
            for risks in risk_matrix.values()
        )
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total des risques", total_risks)
        with col2:
            st.metric("Total des mesures", total_measures)
        
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

# Tab 4: Mesures & Actions
with tab4:
    st.header("Suivi des Mesures et Actions")
    
    # Filtres
    col1, col2, col3 = st.columns(3)
    with col1:
        view_type = st.radio("Vue", ["Par processus", "Par famille", "Par type de mesure"], horizontal=True)
    with col2:
        filter_process = st.selectbox("Filtrer par processus", ["Tous"] + PROCESSES)
    with col3:
        filter_measure = st.selectbox("Filtrer par type", ["Tous"] + list(MEASURE_TYPES.values()))

    # Récupération des données
    df_measures = get_measures_by_process(filter_process)
    
    # Application des filtres supplémentaires
    if filter_measure != "Tous":
        df_measures = df_measures[df_measures["type"] == filter_measure]

    # Organisation de la vue selon le choix
    if view_type == "Par processus":
        unique_processes = df_measures["processus"].str.split(", ").explode().unique()
        for process in sorted(unique_processes):
            process_measures = df_measures[df_measures["processus"].str.contains(process, na=False)]
            with st.expander(f"📎 {process} ({len(process_measures)} mesures)", expanded=True):
                st.dataframe(
                    process_measures[["famille", "risque", "type", "mesure"]], 
                    hide_index=True,
                    use_container_width=True
                )
                
                # Section des actions
                st.markdown("##### Actions à mettre en œuvre")
                action_text = st.text_area("Nouvelle action", key=f"action_{process}")
                col1, col2 = st.columns([1, 4])
                with col1:
                    st.button("Ajouter", key=f"add_action_{process}")

    elif view_type == "Par famille":
        for famille in sorted(df_measures["famille"].unique()):
            family_measures = df_measures[df_measures["famille"] == famille]
            with st.expander(f"📁 {famille} ({len(family_measures)} mesures)", expanded=True):
                st.dataframe(
                    family_measures[["risque", "processus", "type", "mesure"]], 
                    hide_index=True,
                    use_container_width=True
                )

    else:  # Par type de mesure
        for measure_type in sorted(df_measures["type"].unique()):
            type_measures = df_measures[df_measures["type"] == measure_type]
            with st.expander(f"🔖 {measure_type} ({len(type_measures)} mesures)", expanded=True):
                st.dataframe(
                    type_measures[["famille", "risque", "processus", "mesure"]], 
                    hide_index=True,
                    use_container_width=True
                )

    # Statistiques globales
    st.markdown("---")
    st.subheader("Statistiques")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total des mesures", len(df_measures))
    with col2:
        measures_by_type = df_measures["type"].value_counts()
        st.metric("Type le plus utilisé", measures_by_type.index[0] if not measures_by_type.empty else "-")
    with col3:
        st.metric("Familles couvertes", df_measures["famille"].nunique())

# Gestion des notifications
if "notifications" not in st.session_state:
    st.session_state.notifications = []

for notification in st.session_state.notifications:
    st.toast(notification["message"])
st.session_state.notifications = []
