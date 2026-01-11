import {create} from 'zustand';
import axios from 'axios';
import {
    applyNodeChanges,
    applyEdgeChanges,
    addEdge,
} from 'reactflow';
import { apiClient } from '../services/api';

const API_URL = 'http://localhost:5001/api';

const createFlowNode = (blockData) => ({
    id: blockData.id,
    type: 'custom',
    position: { x: blockData.x, y: blockData.y },
    data: { ...blockData, type: blockData.block_type },
    connectable: !blockData.is_collapsed,
    draggable: true, style: blockData.is_collapsed ? { width: '50px', height: '50px' } : {},
});

export const useStore = create((set, get) => ({
    // State
    nodes: [],
    edges: [],
    executionResult: null,
    apiSchemas: {},
    activeBlockId: null,
    executionLogs: [],
    hoveredNodeId: null,
    selectedNodeIds: [],
    isExecuting: false,
    currentProjectId: null,
    currentWorkflowId: null,
    autoSaveTimer: null,

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

            const flowNodes = nodes.map(createFlowNode);
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
        // Trigger auto-save for v2 workflows
        get().scheduleAutoSave();
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
        // Trigger auto-save for v2 workflows
        get().scheduleAutoSave();
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
        // Trigger auto-save for v2 workflows
        get().scheduleAutoSave();
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

            const flowNode = createFlowNode(newNodeData);
            set(state => ({nodes: [...state.nodes, flowNode]}));
            // Trigger auto-save for v2 workflows
            get().scheduleAutoSave();
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
                        return createFlowNode(updatedNodeData);
                    }
                    return n;
                })
            }));
            // Trigger auto-save for v2 workflows
            get().scheduleAutoSave();
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
            // Trigger auto-save for v2 workflows
            get().scheduleAutoSave();
        } catch (error) {
            console.error("Failed to update input value:", error);
        }
    },

    updateOutputValue: async (nodeId, outputKey, value) => {
        try {
            // Call the new backend endpoint
            await axios.post(`${API_URL}/block/update_output_value`, {
                block_id: nodeId,
                output_key: outputKey,
                value: value,
            });

            // Update the local state optimistically
            set(state => ({
                nodes: state.nodes.map(node => {
                    if (node.id === nodeId) {
                        const newOutputs = node.data.outputs.map(out =>
                            out.key === outputKey ? { ...out, value: value } : out
                        );
                        return { ...node, data: { ...node.data, outputs: newOutputs } };
                    }
                    return node;
                })
            }));
        } catch (error) {
            console.error("Failed to update output value:", error);
            alert("Failed to save user input.");
        }
    },

    removeBlock: async (nodeId) => {
        try {
            await axios.post(`${API_URL}/block/remove`, {block_id: nodeId});
            set(state => ({
                nodes: state.nodes.filter(n => n.id !== nodeId),
                edges: state.edges.filter(e => e.source !== nodeId && e.target !== nodeId),
            }));
            // Trigger auto-save for v2 workflows
            get().scheduleAutoSave();
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

    toggleCollapseNode: async (nodeId) => {
        const node = get().nodes.find(n => n.id === nodeId);
        if (!node) return;

        const isCollapsed = !node.data.is_collapsed;

        // Optimistic UI update
        set(state => ({
            nodes: state.nodes.map(n => {
                if (n.id === nodeId) {
                    return {
                        ...n,
                        data: { ...n.data, is_collapsed: isCollapsed },
                        connectable: !isCollapsed,
                        style: isCollapsed ? { width: '50px', height: '50px' } : {}
                    };
                }
                return n;
            })
        }));

        // Sync with backend
        axios.post(`${API_URL}/block/update`, { block_id: nodeId, is_collapsed: isCollapsed })
            .catch(err => console.error("Failed to sync collapse state:", err));
    },

    // --- UI & ANIMATION MANAGEMENT ---

    _updateEdgeAnimations: () => {
        set(state => {
            const hotNodeIds = new Set();

            // During execution, only the active block is "hot"
            if (state.isExecuting) {
                if (state.activeBlockId) hotNodeIds.add(state.activeBlockId);
            } else {
                // Otherwise, consider hovered and selected nodes
                if (state.hoveredNodeId) hotNodeIds.add(state.hoveredNodeId);
                state.selectedNodeIds.forEach(id => hotNodeIds.add(id));
            }

            const newEdges = state.edges.map(edge => {
                const isConnected = hotNodeIds.has(edge.source) || hotNodeIds.has(edge.target);
                const newClassName = isConnected ? 'animated-edge' : '';
                if (edge.className === newClassName) return edge;
                return { ...edge, className: newClassName };
            });

            // Avoid re-render if edges haven't changed class
            const hasChanged = state.edges.length !== newEdges.length ||
                               newEdges.some((edge, i) => edge.className !== state.edges[i].className);

            if (!hasChanged) return {};

            return { edges: newEdges };
        });
    },

    onSelectionChange: ({ nodes: selectedFlowNodes }) => {
        set({ selectedNodeIds: selectedFlowNodes.map(n => n.id) });
        get()._updateEdgeAnimations();
    },

    setHoveredNodeId: (nodeId) => {
        set({ hoveredNodeId: nodeId });
        get()._updateEdgeAnimations();
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
        set({ isExecuting: true, executionLogs: ["Starting execution..."], activeBlockId: null, executionResult: null });

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
                    const trimmedLine = line.trim();
                    if (!trimmedLine) continue;

                    try {
                        const event = JSON.parse(trimmedLine);

                        if (event.type === 'start') {
                            set({ activeBlockId: event.block_id });
                            get()._updateEdgeAnimations();

                            // Handle Dialogue Interactions
                            if (event.block_type === 'DIALOGUE') {
                                let messageContent = event.inputs && event.inputs.message;

                                if (typeof messageContent === 'object' && messageContent !== null) {
                                    messageContent = JSON.stringify(messageContent, null, 2);
                                }
                                
                                // This is a blocking call on the main thread.
                                const userInput = window.prompt(`${messageContent || ''}`, "") || "";
                                
                                // Update the local UI immediately for a responsive feel
                                get().updateOutputValue(event.block_id, 'response', userInput);

                                // Tell the backend to unblock the execution thread.
                                axios.post(`${API_URL}/execution/respond`, {
                                    block_id: event.block_id,
                                    value: userInput
                                });
                            }
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
                            set({ activeBlockId: null, isExecuting: false });
                            get()._updateEdgeAnimations();
                            set(state => ({ executionLogs: [...(state.executionLogs || []), "Execution complete."] }));
                        }
                    } catch (e) {
                        // Skip invalid JSON lines (common in streaming responses)
                        if (trimmedLine.length > 0) {
                            console.warn("Skipping invalid JSON line:", trimmedLine.substring(0, 100));
                        }
                    }
                }
            }
        } catch (error) {
            console.error("Failed to execute graph:", error);
            set({ activeBlockId: null, isExecuting: false });
            get()._updateEdgeAnimations();
            set(state => ({ executionLogs: [...(state.executionLogs || []), `Error: ${error.message}`] }));
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

    // --- NEW V2 API WORKFLOW MANAGEMENT ---
    setCurrentWorkflow: (projectId, workflowId) => {
        set({ currentProjectId: projectId, currentWorkflowId: workflowId });
    },

    loadWorkflowFromV2: async (projectId, workflowId) => {
        try {
            console.log(`Loading workflow ${workflowId} from project ${projectId}`);
            const response = await apiClient.get(`/v2/projects/${projectId}/workflows/${workflowId}`);
            const workflow = response.data;

            // Convert workflow data to ReactFlow format
            const flowNodes = (workflow.data?.nodes || []).map(node => ({
                id: node.id,
                type: 'custom',
                position: { x: node.x || 0, y: node.y || 0 },
                data: node,
            }));

            const flowEdges = workflow.data?.edges || [];

            set({
                nodes: flowNodes,
                edges: flowEdges,
                currentProjectId: projectId,
                currentWorkflowId: workflowId
            });

            console.log('✅ Workflow loaded successfully');
        } catch (error) {
            console.error("Failed to load workflow:", error);
            // Initialize with empty workflow if load fails
            set({ nodes: [], edges: [] });
        }
    },

    saveWorkflowToV2: async () => {
        const state = get();
        const { currentProjectId, currentWorkflowId, nodes, edges } = state;

        if (!currentProjectId || !currentWorkflowId) {
            console.warn('No workflow set, skipping save');
            return;
        }

        try {
            // Convert ReactFlow nodes back to simple data format
            const simpleNodes = nodes.map(node => ({
                id: node.id,
                x: node.position.x,
                y: node.position.y,
                ...node.data
            }));

            await apiClient.put(
                `/v2/projects/${currentProjectId}/workflows/${currentWorkflowId}`,
                {
                    data: {
                        nodes: simpleNodes,
                        edges: edges
                    }
                }
            );

            console.log('✅ Workflow auto-saved');
        } catch (error) {
            console.error("Failed to save workflow:", error);
        }
    },

    scheduleAutoSave: () => {
        const state = get();

        // Clear existing timer
        if (state.autoSaveTimer) {
            clearTimeout(state.autoSaveTimer);
        }

        // Schedule new save after 2 seconds of inactivity
        const timer = setTimeout(() => {
            get().saveWorkflowToV2();
        }, 2000);

        set({ autoSaveTimer: timer });
    },
}));