import React, { useState, useEffect, useCallback } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap,
  useNodesState,
  useEdgesState,
  addEdge
} from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';

// Simple styles for the layout
const containerStyle = { width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column' };
const headerStyle = { padding: '10px', borderBottom: '1px solid #ccc', display: 'flex', gap: '10px', alignItems: 'center' };

const API_BASE = 'http://localhost:5000/api';

export default function App() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [projectName, setProjectName] = useState("Loading...");
  const [executionResult, setExecutionResult] = useState(null);

  // Fetch graph from backend
  const fetchGraph = useCallback(async () => {
    try {
      const res = await axios.get(`${API_BASE}/graph`);
      const { nodes: backendNodes, edges: backendEdges } = res.data;

      // Transform backend nodes to ReactFlow nodes
      const flowNodes = backendNodes.map(node => ({
        id: node.id,
        type: 'default', // Using default for simplicity, ideally custom types
        position: { x: node.x, y: node.y },
        data: { 
          label: (
            <div>
              <strong>{node.name}</strong> ({node.type})
              <hr style={{ margin: '5px 0' }}/>
              <div style={{ fontSize: '10px', textAlign: 'left' }}>
                <div>Inputs: {node.inputs.filter(k => !node.hidden_inputs.includes(k)).join(', ')}</div>
                <div>Outputs: {node.outputs.filter(k => !node.hidden_outputs.includes(k)).join(', ')}</div>
              </div>
              {node.menu_open && <div style={{background: '#eee', padding: 5, marginTop: 5}}>Menu Open</div>}
            </div>
          ) 
        },
        style: { border: '1px solid #777', padding: 10, borderRadius: 5, background: '#fff' }
      }));

      // Transform backend edges to ReactFlow edges
      const flowEdges = backendEdges.map((edge, i) => ({
        id: `e-${i}`,
        source: edge.source,
        target: edge.target,
        label: `${edge.sourceHandle} -> ${edge.targetHandle}`
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch (err) {
      console.error("Failed to fetch graph", err);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    fetchGraph();
    // Poll every few seconds to keep in sync (rudimentary)
    const interval = setInterval(fetchGraph, 5000);
    return () => clearInterval(interval);
  }, [fetchGraph]);

  const handleExecute = async () => {
    try {
      setExecutionResult("Running...");
      const res = await axios.post(`${API_BASE}/execute`);
      setExecutionResult(JSON.stringify(res.data, null, 2));
    } catch (err) {
      setExecutionResult("Error executing graph: " + err.message);
    }
  };

  const handleSave = async () => {
    try {
      const res = await axios.get(`${API_BASE}/project/save`);
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'project.json';
      a.click();
    } catch (err) {
      alert("Failed to save project");
    }
  };

  const handleLoad = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const json = JSON.parse(event.target.result);
        await axios.post(`${API_BASE}/project/load`, json);
        fetchGraph();
        alert("Project loaded!");
      } catch (err) {
        alert("Failed to load project: " + err.message);
      }
    };
    reader.readAsText(file);
  };

  return (
    <div style={containerStyle}>
      <div style={headerStyle}>
        <h3>Block Flow</h3>
        <button onClick={handleExecute}>Run Graph</button>
        <button onClick={handleSave}>Save Project</button>
        <input type="file" onChange={handleLoad} accept=".json" />
        <button onClick={fetchGraph}>Refresh</button>
      </div>
      
      <div style={{ flex: 1, display: 'flex' }}>
        <div style={{ flex: 3, borderRight: '1px solid #ccc' }}>
          <ReactFlow 
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>
        
        <div style={{ flex: 1, padding: '10px', overflow: 'auto', background: '#f5f5f5' }}>
          <h4>Execution Results</h4>
          <pre style={{ whiteSpace: 'pre-wrap', fontSize: '12px' }}>
            {executionResult || "No results yet."}
          </pre>
        </div>
      </div>
    </div>
  );
}