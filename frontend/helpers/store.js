import {create} from 'zustand';
import axios from 'axios';
import {
    applyNodeChanges,
    applyEdgeChanges,
    addEdge,
} from 'reactflow';

const API_URL = 'http://localhost:5001/api';

export const useStore = create((set, get) => ({
    // State
    nodes: [],
    edges: [],
    executionResult: null,
    apiSchemas: {},
    activeBlockId: null,
    executionLogs: [],
    hoveredNodeId: null,

    // --- DATA FETCHING ---
    fetchApiSchemas: async () => {
        try {
            const response = await axios.get(`${API_URL}/schemas`);
            set({apiSchemas: response.data});
        } catch (error) {
            console.error("Failed to fetch API schemas:", error);
        }
    },

    fetchGraph: async () => {
        try {
            const response = await axios.get(`${API_URL}/graph`);
            const {nodes, edges} = response.data;

            const flowNodes = nodes.map(node => ({
                id: node.id,
                type: 'custom',
                position: {x: node.x, y: node.y},
                data: node,
            }));

            set({nodes: flowNodes, edges});
        } catch (error) {
            console.error("Failed to fetch graph:", error);
        }
    },

    // --- REACT FLOW HANDLERS ---
    onNodesChange: (changes) => {
        set({
            nodes: applyNodeChanges(changes, get().nodes),
        });
        changes.forEach(change => {
            if (change.type === 'position' && change.dragging === false) {
                const node = get().nodes.find(n => n.id === change.id);
                if (node) {
                    axios.post(`${API_URL}/block/update`, {block_id: change.id, x: node.position.x, y: node.position.y})
                        .catch(err => console.error("Failed to sync position:", err));
                }
            }
        });
    },

    onEdgesChange: (changes) => {
        const removedEdges = changes.filter(c => c.type === 'remove');
        if (removedEdges.length > 0) {
            const currentEdges = get().edges;
            removedEdges.forEach(removedChange => {
                const edgeToRemove = currentEdges.find(e => e.id === removedChange.id);
                if (edgeToRemove) {
                    axios.post(`${API_URL}/connection/remove`, {
                        source_id: edgeToRemove.source,
                        source_output: edgeToRemove.sourceHandle,
                        target_id: edgeToRemove.target,
                        target_input: edgeToRemove.targetHandle,
                    }).catch(err => {
                        console.error("Failed to remove connection from backend:", err);
                        get().fetchGraph();
                    });
                }
            });
        }
        set({
            edges: applyEdgeChanges(changes, get().edges),
        });
    },

    onConnect: async (connection) => {
        const tempEdgeId = `edge-${connection.source}-${connection.sourceHandle}-${connection.target}-${connection.targetHandle}`;
        const optimisticEdge = {...connection, id: tempEdgeId, type: 'straight'};
        
        set(state => {
            // Ensure inputs only have one connection by removing any existing edge to the target handle
            const filteredEdges = state.edges.filter(e => !(e.target === connection.target && e.targetHandle === connection.targetHandle));
            return {
                edges: addEdge(optimisticEdge, filteredEdges),
            };
        });

        try {
            await axios.post(`${API_URL}/connection/add`, {
                source_id: connection.source,
                source_output: connection.sourceHandle,
                target_id: connection.target,
                target_input: connection.targetHandle,
            });
        } catch (error) {
            console.error("Failed to add connection:", error);
            set(state => ({
                edges: state.edges.filter(e => e.id !== tempEdgeId)
            }));
            get().fetchGraph(); // Refresh to restore previous state if needed
            alert("Failed to create connection. The connection has been rolled back.");
        }
    },

    // --- BLOCK & NODE MANAGEMENT ---
    addBlock: async (type, params = {}) => {
        try {
            // CRITICAL FIX: Instead of refetching, we now use the direct response from the backend.
            // This guarantees the new block is correct, solving the "blank API block" bug.
            const response = await axios.post(`${API_URL}/block/add`, {
                type,
                name: params.name || `New ${type} Block`,
                x: params.x || 150,
                y: params.y || 150,
                ...params
            });
            const newNodeData = response.data.block;

            const flowNode = {
                id: newNodeData.id,
                type: 'custom',
                position: {x: newNodeData.x, y: newNodeData.y},
                data: {...newNodeData, type: newNodeData.block_type},
            };
            set(state => ({nodes: [...state.nodes, flowNode]}));
        } catch (error) {
            console.error("Failed to add block:", error);
        }
    },

    updateNode: async (nodeId, data) => {
        try {
            // CRITICAL FIX: We update the local state precisely using the backend response,
            // avoiding a full graph refetch that would overwrite other optimistic UI changes.
            const response = await axios.post(`${API_URL}/block/update`, {block_id: nodeId, ...data});
            const updatedNodeData = response.data.block;

            set(state => ({
                nodes: state.nodes.map(n => {
                    if (n.id === nodeId) {
                        return {
                            ...n,
                            data: {...updatedNodeData, type: updatedNodeData.block_type}
                        };
                    }
                    return n;
                })
            }));
        } catch (error) {
            console.error("Failed to update node:", error);
        }
    },

    updateInputValue: async (nodeId, inputKey, value) => {
        try {
            await axios.post(`${API_URL}/block/update_input_value`, {
                block_id: nodeId,
                input_key: inputKey,
                value: value,
            });
            set(state => ({
                nodes: state.nodes.map(node => {
                    if (node.id === nodeId) {
                        const newInputs = node.data.inputs.map(input =>
                            input.key === inputKey ? {...input, value: value} : input
                        );
                        return {...node, data: {...node.data, inputs: newInputs}};
                    }
                    return node;
                })
            }));
        } catch (error) {
            console.error("Failed to update input value:", error);
        }
    },

    removeBlock: async (nodeId) => {
        try {
            await axios.post(`${API_URL}/block/remove`, {block_id: nodeId});
            set(state => ({
                nodes: state.nodes.filter(n => n.id !== nodeId),
                edges: state.edges.filter(e => e.source !== nodeId && e.target !== nodeId),
            }));
        } catch (error) {
            console.error("Failed to remove block:", error);
        }
    },

    // --- UI & MENU MANAGEMENT ---
    toggleMenu: (nodeId) => {
        const node = get().nodes.find(n => n.id === nodeId);
        if (node) {
            const newMenuState = !node.data.menu_open;
            set(state => ({
                nodes: state.nodes.map(n =>
                    n.id === nodeId ? {...n, data: {...n.data, menu_open: newMenuState}} : n
                )
            }));
            axios.post(`${API_URL}/block/update`, {block_id: nodeId, menu_open: newMenuState})
                .catch(err => console.error("Failed to sync menu state:", err));
        }
    },

    setHoveredNodeId: (nodeId) => {
        set(state => {
            if (state.hoveredNodeId === nodeId) return {};
            
            const newEdges = state.edges.map(edge => {
                const isConnected = nodeId && (edge.source === nodeId || edge.target === nodeId);
                const newClassName = isConnected ? 'animated-edge' : '';
                if (edge.className === newClassName) return edge;
                return { ...edge, className: newClassName };
            });
            return { hoveredNodeId: nodeId, edges: newEdges };
        });
    },

    togglePortVisibility: (nodeId, key, type) => {
        set(state => ({
            nodes: state.nodes.map(n => {
                if (n.id === nodeId) {
                    const hiddenSet = type === 'input' ? 'hidden_inputs' : 'hidden_outputs';
                    const currentHidden = n.data[hiddenSet] || [];
                    const isHidden = currentHidden.includes(key);
                    const newHidden = isHidden
                        ? currentHidden.filter(k => k !== key)
                        : [...currentHidden, key];
                    return {...n, data: {...n.data, [hiddenSet]: newHidden}};
                }
                return n;
            })
        }));
        axios.post(`${API_URL}/block/toggle_visibility`, {block_id: nodeId, key, type})
            .catch(err => console.error("Failed to sync port visibility:", err));
    },

    // --- EXECUTION ---
    executeGraph: async () => {
        set({ executionLogs: ["Starting execution..."], activeBlockId: null, executionResult: null });

        try {
            const response = await fetch(`${API_URL}/execute`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                buffer += decoder.decode(value, { stream: true });
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep incomplete line

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const event = JSON.parse(line);
                        
                        if (event.type === 'start') {
                            set({ activeBlockId: event.block_id });
                        } else if (event.type === 'progress') {
                            set(state => ({
                                executionLogs: [...(state.executionLogs || []), `Executed ${event.name} (${event.block_type})`]
                            }));

                            // Update node outputs in real-time
                            set(state => ({
                                nodes: state.nodes.map(node => {
                                    if (node.id === event.block_id) {
                                        const newOutputs = node.data.outputs.map(out => ({
                                            ...out,
                                            value: event.outputs[out.key]
                                        }));
                                        return { ...node, data: { ...node.data, outputs: newOutputs } };
                                    }
                                    return node;
                                })
                            }));
                        } else if (event.type === 'error') {
                            set(state => ({
                                executionLogs: [...(state.executionLogs || []), `Error in ${event.name}: ${event.error}`]
                            }));
                        } else if (event.type === 'complete') {
                            set(state => ({
                                activeBlockId: null,
                                executionLogs: [...(state.executionLogs || []), "Execution complete."]
                            }));
                        }
                    } catch (e) {
                        console.error("Error parsing stream line:", e);
                    }
                }
            }
        } catch (error) {
            console.error("Failed to execute graph:", error);
            set(state => ({ 
                executionLogs: [...(state.executionLogs || []), `Error: ${error.message}`] 
            }));
        }
    },

    // --- PROJECT SAVE/LOAD ---
    saveProject: async () => {
        try {
            const response = await axios.get(`${API_URL}/project/save`);
            const projectJson = JSON.stringify(response.data, null, 2);
            const blob = new Blob([projectJson], {type: 'application/json'});

            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'project.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

        } catch (error) {
            console.error("Failed to save project:", error);
            alert("Could not save the project. See console for details.");
        }
    },

    loadProject: async (projectData) => {
        try {
            await axios.post(`${API_URL}/project/load`, projectData);
            get().fetchGraph();
        } catch (error) {
            console.error("Failed to load project:", error);
            alert(`Failed to load project: ${error.response?.data?.error || error.message}`);
        }
    },
}));