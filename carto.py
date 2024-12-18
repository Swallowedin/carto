import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Search, ChevronDown, ChevronRight, Plus, Edit2, Trash2, Save, X, Upload, Download, ChevronLeft } from 'lucide-react';

const RiskManagementTool = () => {
  // États de base
  const [selectedProcess, setSelectedProcess] = useState('all');
  const [selectedMeasureType, setSelectedMeasureType] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRiskFamilies, setSelectedRiskFamilies] = useState({});
  const [selectedRisks, setSelectedRisks] = useState({});
  const [selectedMeasures, setSelectedMeasures] = useState({});
  const [expandedFamilies, setExpandedFamilies] = useState({});
  const [editMode, setEditMode] = useState({});
  const [riskFamiliesData, setRiskFamiliesData] = useState(initialRiskFamilies);
  const [newRiskData, setNewRiskData] = useState({ familyKey: '', name: '', description: '' });
  const [newMeasureData, setNewMeasureData] = useState({ familyKey: '', riskKey: '', type: '', measure: '' });
  const [editingMeasure, setEditingMeasure] = useState(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [showImportModal, setShowImportModal] = useState(false);
  const [bulkImportText, setBulkImportText] = useState('');
  const [importPreview, setImportPreview] = useState(null);

  // Constantes
  const processes = [
    "DIRECTION", "INTERNATIONAL", "PERFORMANCE", "DEVELOPPEMENT_NATIONAL",
    "DEVELOPPEMENT_INTERNATIONAL", "RSE", "GESTION_RISQUES", "FUSAC",
    "INNOV_TRANSFO", "VENTE", "MAGASIN", "LOGISTIQUE", "APPROVISONNEMENT",
    "ACHATS", "SAV", "IMPORT", "FINANCEMENT", "AUTRES_MODES_VENTE",
    "VALO_DECHETS", "QUALITE", "VENTE WEB", "FRANCHISE", "COMPTABILITE",
    "DSI", "RH", "MARKETING", "ORGANISATION", "TECHNIQUE", "JURIDIQUE", "SECURITE"
  ];

  const measureTypes = {
    "D": "Détection",
    "R": "Réduction",
    "A": "Acceptation",
    "F": "Refus",
    "T": "Transfert"
  };

  const measureTypeColors = {
    "D": "bg-blue-100",
    "R": "bg-green-100",
    "A": "bg-yellow-100",
    "F": "bg-red-100",
    "T": "bg-purple-100"
  };

  // Fonctions de gestion des risques
  const toggleRiskFamily = (process, family) => {
    setSelectedRiskFamilies(prev => ({
      ...prev,
      [process]: {
        ...prev[process],
        [family]: !prev[process]?.[family]
      }
    }));
    setExpandedFamilies(prev => ({
      ...prev,
      [`${process}-${family}`]: !prev[`${process}-${family}`]
    }));
  };

  const toggleRisk = (process, family, risk) => {
    setSelectedRisks(prev => ({
      ...prev,
      [process]: {
        ...prev[process],
        [`${family}-${risk}`]: !prev[process]?.[`${family}-${risk}`]
      }
    }));
  };

  const toggleMeasure = (process, family, risk, measureType, measure) => {
    const key = `${process}-${family}-${risk}-${measureType}-${measure}`;
    setSelectedMeasures(prev => ({
      ...prev,
      [key]: !prev[key]
    }));
  };

  // Fonctions d'ajout et modification
  const addNewRisk = (familyKey) => {
    if (!newRiskData.name || !newRiskData.description) return;

    const riskKey = `${familyKey} - ${newRiskData.name}`;
    setRiskFamiliesData(prev => ({
      ...prev,
      [familyKey]: {
        ...prev[familyKey],
        risks: {
          ...prev[familyKey].risks,
          [riskKey]: {
            description: newRiskData.description,
            measures: {
              "D": [],
              "R": [],
              "A": [],
              "F": [],
              "T": []
            }
          }
        }
      }
    }));

    setNewRiskData({ familyKey: '', name: '', description: '' });
    setEditMode(prev => ({ ...prev, [`${familyKey}-new`]: false }));
  };

  const addNewMeasure = (familyKey, riskKey, type) => {
    if (!newMeasureData.measure) return;

    setRiskFamiliesData(prev => ({
      ...prev,
      [familyKey]: {
        ...prev[familyKey],
        risks: {
          ...prev[familyKey].risks,
          [riskKey]: {
            ...prev[familyKey].risks[riskKey],
            measures: {
              ...prev[familyKey].risks[riskKey].measures,
              [type]: [...prev[familyKey].risks[riskKey].measures[type], newMeasureData.measure]
            }
          }
        }
      }
    }));

    setNewMeasureData({ familyKey: '', riskKey: '', type: '', measure: '' });
  };

  const editMeasure = (familyKey, riskKey, type, measureIndex, newValue) => {
    setRiskFamiliesData(prev => ({
      ...prev,
      [familyKey]: {
        ...prev[familyKey],
        risks: {
          ...prev[familyKey].risks,
          [riskKey]: {
            ...prev[familyKey].risks[riskKey],
            measures: {
              ...prev[familyKey].risks[riskKey].measures,
              [type]: prev[familyKey].risks[riskKey].measures[type].map((measure, idx) => 
                idx === measureIndex ? newValue : measure
              )
            }
          }
        }
      }
    }));
    setEditingMeasure(null);
  };

  // Fonctions de suppression
  const deleteRisk = (familyKey, riskKey) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce risque ?')) return;

    setRiskFamiliesData(prev => ({
      ...prev,
      [familyKey]: {
        ...prev[familyKey],
        risks: Object.fromEntries(
          Object.entries(prev[familyKey].risks)
            .filter(([key]) => key !== riskKey)
        )
      }
    }));
  };

  const deleteMeasure = (familyKey, riskKey, type, measureIndex) => {
    setRiskFamiliesData(prev => ({
      ...prev,
      [familyKey]: {
        ...prev[familyKey],
        risks: {
          ...prev[familyKey].risks,
          [riskKey]: {
            ...prev[familyKey].risks[riskKey],
            measures: {
              ...prev[familyKey].risks[riskKey].measures,
              [type]: prev[familyKey].risks[riskKey].measures[type].filter((_, idx) => idx !== measureIndex)
            }
          }
        }
      }
    }));
  };

  // Fonctions d'import/export
  const handleBulkImport = () => {
    try {
      const lines = bulkImportText.split('\n').filter(line => line.trim());
      const newData = { ...riskFamiliesData };

      lines.forEach(line => {
        const [family, risk, description, ...measures] = line.split(';').map(s => s.trim());
        
        if (!newData[family]) {
          newData[family] = {
            name: family,
            risks: {}
          };
        }

        const riskKey = `${family} - ${risk}`;
        newData[family].risks[riskKey] = {
          description,
          measures: {
            "D": measures[0] ? measures[0].split('|') : [],
            "R": measures[1] ? measures[1].split('|') : [],
            "A": measures[2] ? measures[2].split('|') : [],
            "F": measures[3] ? measures[3].split('|') : [],
            "T": measures[4] ? measures[4].split('|') : []
          }
        };
      });

      setRiskFamiliesData(newData);
      setBulkImportText('');
      setShowImportModal(false);
      alert('Import réussi !');
    } catch (error) {
      alert('Erreur dans le format d\'import. Veuillez vérifier vos données.');
    }
  };

  const handleExport = () => {
    const exportLines = [];
    Object.entries(riskFamiliesData).forEach(([family, familyData]) => {
      Object.entries(familyData.risks).forEach(([risk, riskData]) => {
        const measures = [
          riskData.measures.D.join('|'),
          riskData.measures.R.join('|'),
          riskData.measures.A.join('|'),
          riskData.measures.F.join('|'),
          riskData.measures.T.join('|')
        ];
        const line = [
          family,
          risk.replace(`${family} - `, ''),
          riskData.description,
          ...measures
        ].join(';');
        exportLines.push(line);
      });
    });

    const blob = new Blob([exportLines.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'gestion_risques_export.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Fonctions de pagination
  const paginateItems = (items, page, perPage) => {
    const start = (page - 1) * perPage;
    return items.slice(start, start + perPage);
  };

  const getPaginatedData = (data) => {
    const filteredData = Object.entries(data).filter(([family]) => 
      family.toLowerCase().includes(searchTerm.toLowerCase()) ||
      Object.values(data[family].risks).some(risk => 
        risk.description.toLowerCase().includes(searchTerm.toLowerCase())
      )
    );
    return paginateItems(filteredData, currentPage, itemsPerPage);
  };

  // Composants
  const ImportModal = () => (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg p-6 max-w-2xl w-full">
        <h3 className="text-xl font-bold mb-4">Import en masse</h3>
        <p className="text-sm text-gray-600 mb-4">
          Format: famille;risque;description;mesuresD;mesuresR;mesuresA;mesuresF;mesuresT<br />
          Utilisez | pour séparer plusieurs mesures dans une même catégorie
        </p>
        <textarea
          className="w-full h-64 p-2 border rounded mb-4"
          value={bulkImportText}
          onChange={e => setBulkImportText(e.target.value)}
          placeholder="CAD;Cadeaux dérogeant;Description;Mesure D1|Mesure D2;Mesure R1;Mesure A1;Mesure F1;Mesure T1"
        />
        <div className="flex justify-end gap-2">
          <button
            className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
            onClick={() => setShowImportModal(false)}
          >
            Annuler
          </button>
          <button
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            onClick={handleBulkImport}
          >
            Importer
          </button>
        </div>
      </div>
    </div>
  );

  const Pagination = ({ items, itemsPerPage, currentPage, onPageChange }) => {
    const totalPages = Math.ceil(items.length / itemsPerPage);
    const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

    return (
      <div className="flex items-center justify-center gap-2 mt-4">
        <button
          className="p-1 rounded hover:bg-gray-100 disabled:opacity-50"
          onClick={() => onPageChange(Math.max(1, currentPage - 1))}
          disabled={currentPage === 1}
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        {pages.map(page => (
          <button
            key={page}
            className={`px-3 py-1 rounded ${currentPage === page ? 'bg-blue-600 text-white' : 'hover:bg-gray-100'}`}
            onClick={() => onPageChange(page)}
          >
            {page}
          </button>
        ))}
        <button
          className="p-1 rounded hover:bg-gray-100 disabled:opacity-50"
          onClick={() => onPageChange(Math.min(totalPages, currentPage + 1))}
          disabled={currentPage === totalPages}
        >
          <ChevronRight className="w-4 h-4" />
        </button>
        <select
          className="ml-4 p-1 border rounded"
          value={itemsPerPage}
          onChange={e => {
            setItemsPerPage(Number(e.target.value));
            setCurrentPage(1);
          }}
        >
          <option value={5}>5 par page</option>
          <option value={10}>10 par page</option>
          <option value={20}>20 par page</option>
          <option value={50}>50 par page</option>
        </select>
      </div>
    );
  };

  // Rendu principal
  return (
  <Card className="w-full max-w-6xl mx-auto">
    <CardHeader className="bg-gray-50">
      <div className="flex justify-between items-center mb-6">
        <CardTitle className="text-2xl">Gestion des Risques par Processus</CardTitle>
        <div className="flex gap-2">
          <button
            className="px-4 py-2 flex items-center gap-2 text-blue-600 hover:bg-blue-50 rounded"
            onClick={() => setShowImportModal(true)}
          >
            <Upload className="w-4 h-4" />
            Import
          </button>
          <button
            className="px-4 py-2 flex items-center gap-2 text-green-600 hover:bg-green-50 rounded"
            onClick={handleExport}
          >
            <Download className="w-4 h-4" />
            Export
          </button>
        </div>
      </div>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col md:flex-row gap-4 justify-between">
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="text-sm font-medium mb-1 block">Processus</label>
              <select 
                className="w-full p-2 border rounded" 
                value={selectedProcess} 
                onChange={e => setSelectedProcess(e.target.value)}
              >
                <option value="all">Tous les processus</option>
                {processes.map(p => (
                  <option key={p} value={p}>{p.replace(/_/g, ' ')}</option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <label className="text-sm font-medium mb-1 block">Type de Mesure</label>
              <select 
                className="w-full p-2 border rounded" 
                value={selectedMeasureType} 
                onChange={e => setSelectedMeasureType(e.target.value)}
              >
                <option value="all">Toutes</option>
                {Object.entries(measureTypes).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
          </div>
          <div className="relative flex-1 md:max-w-xs">
            <Search className="absolute left-3 top-9 h-4 w-4 text-gray-400" />
            <label className="text-sm font-medium mb-1 block">Recherche</label>
            <input 
              type="text" 
              placeholder="Rechercher..." 
              className="w-full pl-10 p-2 border rounded" 
              value={searchTerm} 
              onChange={e => setSearchTerm(e.target.value)} 
            />
          </div>
        </div>
      </div>
    </CardHeader>
    <CardContent className="mt-4">
      {showImportModal && <ImportModal />}
      {getPaginatedData(riskFamiliesData).map(([familyKey, family]) => (
        <div key={familyKey} className="mb-8 border rounded-lg shadow-sm">
          <div className="bg-gray-50 p-4 rounded-t-lg flex justify-between items-center">
            <h2 className="text-xl font-bold">{family.name}</h2>
            <button
              className="p-2 text-blue-600 hover:bg-blue-50 rounded flex items-center gap-2"
              onClick={() => setEditMode({ ...editMode, [`${familyKey}-new`]: true })}
            >
              <Plus className="w-4 h-4" />
              Nouveau Risque
            </button>
          </div>
          <div className="p-4">
            {editMode[`${familyKey}-new`] && (
              <div className="mb-4 p-4 border rounded bg-gray-50">
                <h3 className="font-medium mb-3">Nouveau Risque</h3>
                <div className="space-y-3">
                  <input
                    type="text"
                    placeholder="Nom du risque"
                    className="w-full p-2 border rounded"
                    value={newRiskData.name}
                    onChange={e => setNewRiskData({ ...newRiskData, name: e.target.value })}
                  />
                  <textarea
                    placeholder="Description"
                    className="w-full p-2 border rounded"
                    value={newRiskData.description}
                    onChange={e => setNewRiskData({ ...newRiskData, description: e.target.value })}
                  />
                  <div className="flex justify-end gap-2">
                    <button
                      className="px-3 py-1 text-gray-600 hover:bg-gray-100 rounded"
                      onClick={() => {
                        setEditMode({ ...editMode, [`${familyKey}-new`]: false });
                        setNewRiskData({ familyKey: '', name: '', description: '' });
                      }}
                    >
                      Annuler
                    </button>
                    <button
                      className="px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700"
                      onClick={() => addNewRisk(familyKey)}
                    >
                      Ajouter
                    </button>
                  </div>
                </div>
              </div>
            )}
            {Object.entries(family.risks).map(([riskKey, risk]) => (
              <div key={riskKey} className="mb-4 border-b pb-4">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="text-lg font-semibold">{riskKey}</h3>
                    <p className="text-gray-600">{risk.description}</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      className="p-1 text-gray-500 hover:bg-gray-100 rounded"
                      onClick={() => setEditMode({ ...editMode, [riskKey]: true })}
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                    <button
                      className="p-1 text-red-500 hover:bg-red-50 rounded"
                      onClick={() => deleteRisk(familyKey, riskKey)}
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                {Object.entries(risk.measures).map(([measureType, measures]) => (
                  <div key={measureType} className={`mt-3 p-3 rounded ${measureTypeColors[measureType]}`}>
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="font-medium">{measureTypes[measureType]}</h4>
                      <button
                        className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                        onClick={() => setNewMeasureData({
                          familyKey,
                          riskKey,
                          type: measureType,
                          measure: ''
                        })}
                      >
                        <Plus className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="space-y-2">
                      {measures.map((measure, idx) => (
                        <div key={idx} className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <input
                              type="checkbox"
                              checked={selectedMeasures[`${selectedProcess}-${familyKey}-${riskKey}-${measureType}-${measure}`] || false}
                              onChange={() => toggleMeasure(selectedProcess, familyKey, riskKey, measureType, measure)}
                              className="w-4 h-4"
                            />
                            {editingMeasure === `${familyKey}-${riskKey}-${measureType}-${idx}` ? (
                              <input
                                type="text"
                                className="flex-1 p-1 border rounded"
                                value={measure}
                                onChange={e => editMeasure(familyKey, riskKey, measureType, idx, e.target.value)}
                                onBlur={() => setEditingMeasure(null)}
                                autoFocus
                              />
                            ) : (
                              <span>{measure}</span>
                            )}
                          </div>
                          <div className="flex gap-1">
                            <button
                              className="p-1 text-gray-500 hover:bg-gray-100 rounded"
                              onClick={() => setEditingMeasure(`${familyKey}-${riskKey}-${measureType}-${idx}`)}
                            >
                              <Edit2 className="w-3 h-3" />
                            </button>
                            <button
                              className="p-1 text-red-500 hover:bg-red-50 rounded"
                              onClick={() => deleteMeasure(familyKey, riskKey, measureType, idx)}
                            >
                              <Trash2 className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      ))}
                      {newMeasureData.familyKey === familyKey &&
                       newMeasureData.riskKey === riskKey &&
                       newMeasureData.type === measureType && (
                        <div className="flex items-center gap-2 mt-2">
                          <input
                            type="text"
                            className="flex-1 p-2 border rounded"
                            placeholder="Nouvelle mesure..."
                            value={newMeasureData.measure}
                            onChange={e => setNewMeasureData({ ...newMeasureData, measure: e.target.value })}
                          />
                          <button
                            className="p-1 text-green-600 hover:bg-green-50 rounded"
                            onClick={() => addNewMeasure(familyKey, riskKey, measureType)}
                          >
                            <Save className="w-4 h-4" />
                          </button>
                          <button
                            className="p-1 text-red-500 hover:bg-red-50 rounded"
                            onClick={() => setNewMeasureData({ familyKey: '', riskKey: '', type: '', measure: '' })}
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      ))}
      <Pagination 
        items={Object.entries(riskFamiliesData)}
        itemsPerPage={itemsPerPage}
        currentPage={currentPage}
        onPageChange={setCurrentPage}
      />
    </CardContent>
  </Card>
);
