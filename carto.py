import streamlit as st

# Configuration de la page DOIT être le premier appel Streamlit
st.set_page_config(
    page_title="Gestion des Risques",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Autres imports
import pandas as pd
from datetime import datetime
import json
import base64
import plotly.graph_objects as go
from collections import defaultdict

# Style CSS
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .element-container {
        margin-bottom: 0.5rem;
    }
    .stButton>button {
        padding: 0.25rem 0.5rem;
        font-size: 0.8rem;
    }
    .stMarkdown {
        margin-bottom: 0.5rem;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 0.9rem;
        margin-bottom: 0rem;
    }
    .streamlit-expanderHeader {
        padding: 0.5rem;
    }
    .stTextInput>div>div>input {
        padding: 0.25rem 0.5rem;
        line-height: 1;
    }
    </style>
""", unsafe_allow_html=True)

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

# Barre latérale
with st.sidebar:
    with st.container():
        st.header("Filtres", divider='blue')
        selected_process = st.selectbox(
            "Processus", 
            ["Tous"] + PROCESSES, 
            help="Filtrer les risques par processus"
        )
        selected_measure_type = st.selectbox(
            "Type de Mesure", 
            ["Tous"] + list(MEASURE_TYPES.values()),
            help="Filtrer par type de mesure (Détection, Réduction, etc.)"
        )
        search_term = st.text_input(
            "Recherche",
            placeholder="Rechercher un risque...",
            help="Rechercher dans les risques et leurs descriptions"
        )
    
    # Statistiques compactes
    st.header("Statistiques", divider='blue')
    stats = get_risk_stats()
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Risques", stats["total_risks"])
    with col2:
        st.metric("Mesures", stats["total_measures"])

# En-tête principale et actions
header_col1, header_col2, header_col3 = st.columns([2, 1, 1])
with header_col1:
    st.header("Gestion des Risques")
with header_col2:
    uploaded_file = st.file_uploader("Import CSV", type="csv", label_visibility="collapsed")
    if uploaded_file and import_data(uploaded_file):
        st.success("Import réussi")
with header_col3:
    if st.button("Exporter CSV", use_container_width=True):
        csv_data = export_data()
        st.download_button(
            "Télécharger",
            csv_data,
            f"export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            "text/csv"
        )

# Onglets principaux
tab1, tab2, tab3 = st.tabs([
    "📊 Risques | Gestion par famille",
    "🔄 Processus | Vue par processus",
    "🏢 Service | Impact par service"
])

# Contenu de l'onglet Risques
with tab1:
    for family_key, family_data in st.session_state.risk_families.items():
        with st.expander(f"{family_data['name']}", expanded=False):
            # Formulaire d'ajout de risque
            with st.form(key=f"risk_form_{family_key}"):
                form_col1, form_col2 = st.columns([3, 1])
                with form_col1:
                    risk_name = st.text_input(
                        "Nom du risque",
                        placeholder="Ex: Cadeaux dérogeants",
                        help="Nom court et descriptif du risque"
                    )
                    risk_desc = st.text_input(
                        "Description",
                        placeholder="Description détaillée du risque...",
                        help="Expliquez le contexte et les implications"
                    )
                with form_col2:
                    selected_processes = st.multiselect(
                        "Processus concernés",
                        PROCESSES,
                        help="Sélectionnez tous les processus impactés"
                    )

            # Liste des risques existants
            for risk_key, risk_data in family_data["risks"].items():
                if selected_process != "Tous" and selected_process not in risk_data.get("processes", []):
                    continue
                    
                with st.container():
                    risk_col1, risk_col2 = st.columns([6, 1])
                    with risk_col1:
                        st.markdown(f"**{risk_key}**")
                        st.caption(risk_data["description"])
                    with risk_col2:
                        if st.button("🗑️", key=f"del_{risk_key}"):
                            delete_risk(family_key, risk_key)
                            st.rerun()

                    # Mesures par type
                    for measure_type, measure_name in MEASURE_TYPES.items():
                        if selected_measure_type != "Tous" and measure_name != selected_measure_type:
                            continue
                            
                        with st.container():
                            st.write(f"**{measure_name}**")
                            
                            # Ajout d'une nouvelle mesure
                            with st.form(key=f"measure_form_{risk_key}_{measure_type}"):
                                new_measure = st.text_input(
                                    "Nouvelle mesure", 
                                    key=f"new_measure_{risk_key}_{measure_type}"
                                )
                                if st.form_submit_button("Ajouter"):
                                    add_measure(family_key, risk_key, measure_type, new_measure)
                                    st.rerun()
                            
                            # Liste des mesures existantes
                            measures = risk_data["measures"][measure_type]
                            for i, measure in enumerate(measures):
                                cols = st.columns([10, 1])
                                with cols[0]:
                                    st.write(f"- {measure}")
                                with cols[1]:
                                    if st.button("🗑️", key=f"delete_measure_{risk_key}_{measure_type}_{i}"):
                                        delete_measure(family_key, risk_key, measure_type, i)
                                        st.rerun()

# Fonctions utilitaires pour les vues
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

def get_service_risk_matrix():
    """Crée une matrice de risques par service"""
    matrix = defaultdict(lambda: defaultdict(list))
    for family_key, family_data in st.session_state.risk_families.items():
        for risk_key, risk_data in family_data["risks"].items():
            for process in risk_data.get("processes", []):
                matrix[process][family_key].append({
                    "risk_key": risk_key,
                    "description": risk_data["description"],
                    "measures": risk_data["measures"],
                    "measure_count": sum(len(m) for m in risk_data["measures"].values())
                })
    return matrix

# Vue par Processus (Tab 2)
with tab2:
    st.header("Vue par Processus")
    
    # Sélection du processus
    selected_process_view = st.selectbox(
        "Sélectionner un processus",
        PROCESSES,
        key="process_view_selector"
    )
    
    # Affichage des statistiques du processus
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
                process_stats["measures_by_type"][measure_type],
                help=f"Nombre de mesures de type {measure_name}"
            )
    
    # Liste des risques associés
    st.subheader("Risques associés")
    process_risks = get_risks_by_process(selected_process_view)
    
    # Groupement par famille
    risks_by_family = defaultdict(list)
    for risk in process_risks:
        risks_by_family[risk["family"]].append(risk)
    
    # Affichage par famille
    for family, risks in risks_by_family.items():
        with st.expander(f"{family} ({len(risks)} risques)", expanded=True):
            for risk in risks:
                st.markdown(f"### {risk['risk']}")
                st.write(risk["description"])
                
                # Mesures avec possibilité d'édition
                for measure_type, measures in risk["measures"].items():
                    if measures:  # N'afficher que les types avec des mesures
                        st.write(f"**{MEASURE_TYPES[measure_type]}**")
                        for measure in measures:
                            st.write(f"- {measure}")
                
                # Ajout rapide de mesure
                with st.form(key=f"quick_measure_{risk['risk']}"):
                    cols = st.columns([3, 1])
                    with cols[0]:
                        new_measure = st.text_input(
                            "Nouvelle mesure",
                            key=f"quick_new_measure_{risk['risk']}"
                        )
                    with cols[1]:
                        measure_type = st.selectbox(
                            "Type",
                            MEASURE_TYPES.keys(),
                            format_func=lambda x: MEASURE_TYPES[x],
                            key=f"quick_measure_type_{risk['risk']}"
                        )
                    if st.form_submit_button("Ajouter"):
                        add_measure(risk["family"], risk["risk"], measure_type, new_measure)
                        st.rerun()

# Vue par Service (Tab 3)
with tab3:
    st.header("Vue par Service")
    
    # Matrice de risques par service
    risk_matrix = get_service_risk_matrix()
    
    # Sélection du service
    selected_service = st.selectbox(
        "Sélectionner un service",
        PROCESSES,
        key="service_view_selector"
    )
    
    if selected_service in risk_matrix:
        # Statistiques du service
        service_risks = risk_matrix[selected_service]
        total_risks = sum(len(risks) for risks in service_risks.values())
        total_measures = sum(
            sum(risk["measure_count"] for risk in risks)
            for risks in service_risks.values()
        )
        
        # Métriques du service
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total des risques", total_risks)
        with col2:
            st.metric("Total des mesures", total_measures)
        
        # Affichage par famille de risques
        for family, risks in service_risks.items():
            with st.expander(f"{family} ({len(risks)} risques)", expanded=True):
                # Tableau récapitulatif
                headers = ["Risque", "Mesures", "Actions"]
                data = []
                for risk in risks:
                    measures_by_type = {
                        measure_type: len(measures)
                        for measure_type, measures in risk["measures"].items()
                    }
                    
                    measure_summary = " | ".join(
                        f"{MEASURE_TYPES[t]}: {count}"
                        for t, count in measures_by_type.items()
                        if count > 0
                    )
                    
                    data.append([
                        risk["risk_key"],
                        measure_summary,
                        st.button("Gérer", key=f"manage_{risk['risk_key']}")
                    ])
                
                # Création du tableau avec Pandas pour un meilleur formatage
                df = pd.DataFrame(data, columns=headers)
                st.table(df)
                
                # Zone d'actions rapides
                st.subheader("Actions rapides")
                cols = st.columns(len(MEASURE_TYPES))
                for i, (measure_type, measure_name) in enumerate(MEASURE_TYPES.items()):
                    with cols[i]:
                        st.button(
                            f"Ajouter {measure_name}",
                            key=f"quick_add_{family}_{measure_type}"
                        )
# Configuration des styles et de l'apparence
st.markdown("""
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .element-container {
        margin-bottom: 0.5rem;
    }
    .stButton>button {
        padding: 0.25rem 0.5rem;
        font-size: 0.8rem;
    }
    .stMarkdown {
        margin-bottom: 0.5rem;
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-size: 0.9rem;
        margin-bottom: 0rem;
    }
    .streamlit-expanderHeader {
        padding: 0.5rem;
    }
    .stTextInput>div>div>input {
        padding: 0.25rem 0.5rem;
        line-height: 1;
    }
    </style>
""", unsafe_allow_html=True)

# Configuration des notifications et alertes
if "notifications" not in st.session_state:
    st.session_state.notifications = []

def add_notification(message, type="info"):
    st.session_state.notifications.append({
        "message": message,
        "type": type,
        "timestamp": datetime.now()
    })

# Affichage des notifications
if st.session_state.notifications:
    with st.container():
        for notif in st.session_state.notifications:
            if notif["type"] == "success":
                st.success(notif["message"])
            elif notif["type"] == "error":
                st.error(notif["message"])
            elif notif["type"] == "warning":
                st.warning(notif["message"])
            else:
                st.info(notif["message"])
    
    # Nettoyage des anciennes notifications
    if st.button("Effacer les notifications"):
        st.session_state.notifications = []

# Configuration des paramètres de l'application
if "config" not in st.session_state:
    st.session_state.config = {
        "auto_save": True,
        "show_stats": True,
        "default_view": "risks",
        "theme": "light"
    }

# Interface de configuration dans la barre latérale
with st.sidebar:
    st.markdown("---")
    st.subheader("Paramètres")
    
    # Sauvegarde automatique
    st.session_state.config["auto_save"] = st.checkbox(
        "Sauvegarde automatique",
        value=st.session_state.config["auto_save"]
    )
    
    # Affichage des statistiques
    st.session_state.config["show_stats"] = st.checkbox(
        "Afficher les statistiques",
        value=st.session_state.config["show_stats"]
    )
    
    # Vue par défaut
    st.session_state.config["default_view"] = st.selectbox(
        "Vue par défaut",
        ["risks", "process", "service"],
        format_func=lambda x: {
            "risks": "Risques",
            "process": "Processus",
            "service": "Service"
        }[x],
        index=["risks", "process", "service"].index(st.session_state.config["default_view"])
    )
    
    # Thème
    st.session_state.config["theme"] = st.selectbox(
        "Thème",
        ["light", "dark"],
        format_func=lambda x: x.capitalize(),
        index=["light", "dark"].index(st.session_state.config["theme"])
    )

# Sauvegarde automatique si activée
if st.session_state.config["auto_save"]:
    if "last_save" not in st.session_state:
        st.session_state.last_save = datetime.now()
    
    if (datetime.now() - st.session_state.last_save).seconds > 300:  # Sauvegarde toutes les 5 minutes
        save_to_json()
        st.session_state.last_save = datetime.now()
        add_notification("Sauvegarde automatique effectuée", "info")
