'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap,
  useNodesState,
  useEdgesState,
  Panel,
  Handle,
  Position
} from 'reactflow';
import 'reactflow/dist/style.css';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

// --- Custom Node Component ---
const CustomNode = ({ data, id }) => {
  const [schemas, setSchemas] = useState({});
  
  // Fetch schemas only if it's an API block
  useEffect(() => {
    if (data.type === 'API' && Object.keys(schemas).length === 0) {
      axios.get(`${API_BASE}/schemas`).then(res => setSchemas(res.data));
    }
  }, [data.type, schemas]);

  const handleSchemaChange = async (e) => {
    const newSchema = e.target.value;
    try {
      await axios.post(`${API_BASE}/block/update`, {
        block_id: id,
        schema_key: newSchema
      });
      // Trigger a refresh in parent (handled by polling for now)
    } catch (err) {
      console.error("Failed to update schema", err);
    }
  };

  const visibleInputs = data.inputs.filter(k => !data.hidden_inputs.includes(k));
  const visibleOutputs = data.outputs.filter(k => !data.hidden_outputs.includes(k));

  return (
    <div className="bg-white border border-gray-400 rounded shadow-md min-w-[200px]">
      {/* Header */}
      <div className="bg-gray-100 border-b border-gray-300 p-2 rounded-t font-bold text-sm flex justify-between items-center">
        <span>{data.name}</span>
        <span className="text-[10px] text-gray-500 uppercase">{data.type}</span>
      </div>

      {/* API Schema Selector */}
      {data.type === 'API' && (
        <div className="p-2 border-b border-gray-200 bg-gray-50">
          <select 
            className="w-full text-xs border rounded p-1"
            value={data.extra?.schema_key || 'custom'}
            onChange={handleSchemaChange}
          >
            {Object.entries(schemas).map(([key, schema]) => (
              <option key={key} value={key}>{schema.name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Body: Inputs (Left) and Outputs (Right) */}
      <div className="flex flex-row p-2 gap-4">
        {/* Inputs Column */}
        <div className="flex flex-col gap-2 flex-1">
          {visibleInputs.map((key) => (
            <div key={key} className="relative flex items-center h-6">
              <Handle 
                type="target" 
                position={Position.Left} 
                id={key} 
                className="!bg-blue-500 !w-3 !h-3 !-left-[18px]" 
              />
              <span className="text-xs text-gray-700 ml-1">{key}</span>
            </div>
          ))}
          {visibleInputs.length === 0 && <div className="text-[10px] text-gray-400 italic">No Inputs</div>}
        </div>

        {/* Outputs Column */}
        <div className="flex flex-col gap-2 flex-1 items-end">
          {visibleOutputs.map((key) => (
            <div key={key} className="relative flex items-center h-6 justify-end">
              <span className="text-xs text-gray-700 mr-1">{key}</span>
              <Handle 
                type="source" 
                position={Position.Right} 
                id={key} 
                className="!bg-green-500 !w-3 !h-3 !-right-[18px]" 
              />
            </div>
          ))}
          {visibleOutputs.length === 0 && <div className="text-[10px] text-gray-400 italic">No Outputs</div>}
        </div>
      </div>
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

export default function Home() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [executionResult, setExecutionResult] = useState(null);
  const [contextMenu, setContextMenu] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  
  const isDraggingRef = useRef(false);

  const fetchGraph = useCallback(async () => {
    if (isDraggingRef.current) return;

    try {
      const res = await axios.get(`${API_BASE}/graph`);
      const { nodes: backendNodes, edges: backendEdges } = res.data;

      const flowNodes = backendNodes.map(node => ({
        id: node.id,
        type: 'custom', // Use our custom node component
        position: { x: node.x, y: node.y },
        data: { 
          name: node.name,
          type: node.type,
          inputs: node.inputs,
          outputs: node.outputs,
          hidden_inputs: node.hidden_inputs,
          hidden_outputs: node.hidden_outputs,
          extra: node.extra
        }
      }));

      const flowEdges = backendEdges.map((edge, i) => ({
        id: `e-${i}`,
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle,
        targetHandle: edge.targetHandle,
        animated: true,
        style: { stroke: '#555' }
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch (err) {
      console.error("Failed to fetch graph", err);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    fetchGraph();
    const interval = setInterval(fetchGraph, 2000); // Poll faster for UI updates
    return () => clearInterval(interval);
  }, [fetchGraph]);

  const onNodeDragStart = () => {
    isDraggingRef.current = true;
  };

  const onNodeDragStop = async (event, node) => {
    isDraggingRef.current = false;
    try {
      await axios.post(`${API_BASE}/block/update`, {
        block_id: node.id,
        x: node.position.x,
        y: node.position.y
      });
    } catch (err) {
      console.error("Failed to update node position", err);
    }
  };

  const onConnect = async (params) => {
    try {
      await axios.post(`${API_BASE}/connection/add`, {
        source_id: params.source,
        source_output: params.sourceHandle,
        target_id: params.target,
        target_input: params.targetHandle
      });
      fetchGraph();
    } catch (err) {
      alert("Failed to connect: " + err.message);
    }
  };

  const onNodeContextMenu = (event, node) => {
    event.preventDefault();
    setSelectedNode(node);
    setContextMenu({
      x: event.clientX,
      y: event.clientY,
    });
  };

  const onPaneClick = () => {
    setContextMenu(null);
    setSelectedNode(null);
  };

  const handleAddBlock = async (type) => {
    try {
      await axios.post(`${API_BASE}/block/add`, {
        type: type,
        name: `New ${type}`,
        x: 100,
        y: 100
      });
      fetchGraph();
    } catch (err) {
      alert("Failed to add block: " + err.message);
    }
  };

  const handleDeleteBlock = async () => {
    if (!selectedNode) return;
    try {
      await axios.post(`${API_BASE}/block/remove`, {
        block_id: selectedNode.id
      });
      setContextMenu(null);
      fetchGraph();
    } catch (err) {
      alert("Failed to delete block: " + err.message);
    }
  };

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
    <main className="flex min-h-screen flex-col" onClick={onPaneClick}>
      <div className="flex items-center gap-4 p-4 border-b bg-white shadow-sm z-10">
        <h1 className="text-xl font-bold">Block Flow</h1>
        <div className="flex gap-2 ml-auto">
          <button onClick={handleExecute} className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600">Run</button>
          <button onClick={handleSave} className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600">Save</button>
          <label className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 cursor-pointer">
            Load
            <input type="file" onChange={handleLoad} accept=".json" className="hidden" />
          </label>
          <button onClick={fetchGraph} className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600">Refresh</button>
        </div>
      </div>

      <div className="flex flex-1 h-[calc(100vh-73px)]">
        <div className="flex-1 border-r relative">
          <ReactFlow 
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeDragStart={onNodeDragStart}
            onNodeDragStop={onNodeDragStop}
            onNodeContextMenu={onNodeContextMenu}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap />
            <Panel position="top-left" className="bg-white p-2 rounded shadow-md border flex flex-col gap-2">
              <div className="font-bold text-sm mb-1">Add Block</div>
              <button onClick={() => handleAddBlock('API')} className="text-xs px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-left">API Block</button>
              <button onClick={() => handleAddBlock('LOGIC')} className="text-xs px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-left">Logic Block</button>
              <button onClick={() => handleAddBlock('REACT')} className="text-xs px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-left">React Block</button>
              <button onClick={() => handleAddBlock('TRANSFORM')} className="text-xs px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-left">Transform Block</button>
              <button onClick={() => handleAddBlock('STRING_BUILDER')} className="text-xs px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-left">String Builder</button>
            </Panel>
          </ReactFlow>

          {contextMenu && (
            <div 
              style={{ top: contextMenu.y, left: contextMenu.x }} 
              className="absolute z-50 bg-white border shadow-lg rounded p-2 flex flex-col gap-1 min-w-[120px]"
            >
              <div className="text-xs font-bold text-gray-500 px-2 pb-1 border-b mb-1">Actions</div>
              <button 
                onClick={handleDeleteBlock}
                className="text-sm text-red-600 hover:bg-red-50 px-2 py-1 rounded text-left"
              >
                Delete Block
              </button>
            </div>
          )}
        </div>
        
        <div className="w-1/4 bg-gray-50 p-4 overflow-auto border-l shadow-inner">
          <h2 className="font-bold mb-2 text-gray-700">Execution Results</h2>
          <pre className="bg-white p-4 rounded border text-xs overflow-auto whitespace-pre-wrap">
            {executionResult || "No results yet."}
          </pre>
        </div>
      </div>
    </main>
  );
}