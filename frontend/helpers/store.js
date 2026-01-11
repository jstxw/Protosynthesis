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
    data: {
        ...blockData,
        type: blockData.type || blockData.block_type // Ensure type is always present
    },
    connectable: !blockData.is_collapsed,
    draggable: true, style: blockData.is_collapsed ? { width: '50px', height: '50px' } : {},
    // Ensure selection flag is present so ReactFlow and our store stay in sync
    selected: false,
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
    selectedNodeId: null,
    isExecuting: false,
    currentProjectId: null,
    currentWorkflowId: null,
    autoSaveTimer: null,
    
    // --- THEME & EDITOR ---
    editorTheme: {
        base: 'vs-dark',
        inherit: true,
        rules: [
            { token: 'comment', foreground: '6A9955' },
            { token: 'keyword', foreground: 'C586C0' },
            { token: 'identifier', foreground: '9CDCFE' },
            { token: 'string', foreground: 'CE9178' },
            { token: 'delimiter', foreground: 'D4D4D4' },
        ],
        colors: {
            'editor.background': '#1E1E1E',
            'editor.foreground': '#D4D4D4',
            'editor.lineHighlightBackground': '#2F3337',
        }
    },

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
            
            // Auto-select React node if present
            const reactNode = flowNodes.find(n => n.data && (n.data.type === 'REACT' || n.data.block_type === 'REACT'));
            if (reactNode) {
                set({ selectedNodeId: reactNode.id });
            }
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
                // Determine if we are in V2 mode or Legacy mode
                const { currentProjectId, currentWorkflowId, nodes } = get();
                // If in V2 mode, we only rely on auto-save (saveWorkflowToV2).
                // We do NOT call the legacy /block/update endpoint to avoid specific block handling conflicts
                // or needing to keep 'current_project' in main.py in sync with partial updates.
                if (!currentProjectId || !currentWorkflowId) {
                     const node = nodes.find(n => n.id === change.id);
                     if (node) {
                         axios.post(`${API_URL}/block/update`, {block_id: change.id, x: node.position.x, y: node.position.y})
                             .catch(err => console.error("Failed to sync position:", err));
                     }
                }
            }
        });
        // Trigger auto-save for v2 workflows
        get().scheduleAutoSave();
    },

    onEdgesChange: (changes) => {
        const removedEdges = changes.filter(c => c.type === 'remove');
        if (removedEdges.length > 0) {
            const { currentProjectId, currentWorkflowId, edges } = get();

            // Only use legacy removal if NOT in V2 mode
            if (!currentProjectId || !currentWorkflowId) {
                removedEdges.forEach(removedChange => {
                    const edgeToRemove = edges.find(e => e.id === removedChange.id);
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

        // Only call legacy endpoint if NOT in V2 mode
        const { currentProjectId, currentWorkflowId } = get();
        if (!currentProjectId || !currentWorkflowId) {
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
        }
        // Trigger auto-save for v2 workflows
        get().scheduleAutoSave();
    },

    // --- BLOCK & NODE MANAGEMENT ---
    addBlock: async (type, params = {}) => {
        const { currentProjectId, currentWorkflowId } = get();

        // Prevent adding more than one REACT I/O block
        if (type === 'REACT') {
            const exists = get().nodes.some(n => (n.data && (n.data.type === 'REACT' || n.data.block_type === 'REACT')));
            if (exists) {
                // Inform the user and early return — only one React I/O node allowed
                if (typeof window !== 'undefined') {
                    window.alert('A React I/O block already exists in this workflow. Only one is allowed.');
                }
                return;
            }
        }

        // V2 Mode: Create local node and save entire graph
        if (currentProjectId && currentWorkflowId) {
            // In V2 workflow mode we rely on backend-initialized nodes; we don't need a local newNodeId here.
            // Build minimal node metadata for local creation (we don't reuse it directly here)
             try {
                // Use legacy endpoint just to get a properly initialized block structure
                // But we don't care if it "saves" to the ephemeral current_project
                const response = await axios.post(`${API_URL}/block/add`, {
                    type,
                    name: params.name || `New ${type} Block`,
                    x: params.x || 150,
                    y: params.y || 150,
                    ...params
                });
                const initializedBlock = response.data.block;
                // Force a new ID if needed to ensure uniqueness in V2 context, though backend generated one.

                const flowNode = createFlowNode(initializedBlock);
                set(state => ({nodes: [...state.nodes, flowNode]}));
                get().selectNode(flowNode.id);
                get().scheduleAutoSave();
             } catch (error) {
                 console.error("Failed to init block via backend:", error);
             }
             return;
        }

        // Legacy Mode
        try {
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
            // Trigger auto-save for v2 workflows (if applicable, though we are in legacy block)
            get().selectNode(flowNode.id);
            get().scheduleAutoSave();
        } catch (error) {
            console.error("Failed to add block:", error);
        }
    },

    updateNode: async (nodeId, data) => {
        const { currentProjectId, currentWorkflowId } = get();

        // Optimistic update first
        set(state => ({
            nodes: state.nodes.map(n => {
                if (n.id === nodeId) {
                    // Merge data into n.data
                    return { ...n, data: { ...n.data, ...data } };
                }
                return n;
            })
        }));
        get().scheduleAutoSave();

        // If Legacy mode, sync to backend endpoint
        if (!currentProjectId || !currentWorkflowId) {
            try {
                await axios.post(`${API_URL}/block/update`, {block_id: nodeId, ...data});
                // ... legacy logic
            } catch (error) {
                console.error("Failed to update node:", error);
            }
        }
    },

    updateInputValue: async (nodeId, inputKey, value) => {
        // Optimistic update
        set(state => ({
            nodes: state.nodes.map(node => {
                if (node.id === nodeId) {
                    const newInputs = (node.data.inputs || []).map(input =>
                        input.key === inputKey ? {...input, value: value} : input
                    );
                    return {...node, data: {...node.data, inputs: newInputs}};
                }
                return node;
            })
        }));
        get().scheduleAutoSave();

        // Legacy sync
        const { currentProjectId, currentWorkflowId } = get();
        if (!currentProjectId || !currentWorkflowId) {
            try {
                await axios.post(`${API_URL}/block/update_input_value`, {
                    block_id: nodeId,
                    input_key: inputKey,
                    value: value,
                });
            } catch (error) {
                console.error("Failed to update input value:", error);
            }
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
        // Optimistic removal
        set(state => ({
            nodes: state.nodes.filter(n => n.id !== nodeId),
            edges: state.edges.filter(e => e.source !== nodeId && e.target !== nodeId),
        }));
        get().scheduleAutoSave();

        const { currentProjectId, currentWorkflowId } = get();
        // Legacy Sync
        if (!currentProjectId || !currentWorkflowId) {
            try {
                await axios.post(`${API_URL}/block/remove`, {block_id: nodeId});
            } catch (error) {
                console.error("Failed to remove block:", error);
            }
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
                // state.selectedNodeIds.forEach(id => hotNodeIds.add(id));
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

    onSelectionChange: ({ nodes: selectedNodes }) => {
        const selectedIds = (selectedNodes || []).map(n => n.id);
        
        // Editor Logic: Always point to React Node if it exists
        const reactNode = get().nodes.find(n => n.data && (n.data.type === 'REACT' || n.data.block_type === 'REACT'));
        let editorTargetId = null;
        if (reactNode) {
            editorTargetId = reactNode.id;
        } else {
            editorTargetId = selectedIds.length === 1 ? selectedIds[0] : null;
        }
        
        const activeId = selectedIds.length === 1 ? selectedIds[0] : null;

        // Update node.selected flags so other parts of the UI (and ReactFlow) stay consistent
        set(state => ({
            nodes: state.nodes.map(n => {
                const shouldBeSelected = selectedIds.includes(n.id);
                if (n.selected === shouldBeSelected) return n;
                return { ...n, selected: shouldBeSelected };
            }),
            selectedNodeIds: selectedIds,
            activeBlockId: state.isExecuting ? state.activeBlockId : activeId, 
            selectedNodeId: editorTargetId // Sync selectedNodeId for ReactIDE (forced to React Node if present)
        }));
    },

    // Programmatically select nodes. If `additive` is true, toggle/add to existing selection
    selectNode: (nodeId, additive = false) => {
        set(state => {
            let newSelectedIds;

            if (additive) {
                // Toggle selection of the clicked node while preserving others
                const currentlySelected = state.selectedNodeIds.includes(nodeId);
                newSelectedIds = currentlySelected
                    ? state.selectedNodeIds.filter(id => id !== nodeId)
                    : [...state.selectedNodeIds, nodeId];
            } else {
                // Default: single selection or clear
                newSelectedIds = nodeId ? [nodeId] : [];
            }

            // Editor Logic: Always point to React Node if it exists
            const reactNode = state.nodes.find(n => n.data && (n.data.type === 'REACT' || n.data.block_type === 'REACT'));
            let editorTargetId = null;
            if (reactNode) {
                editorTargetId = reactNode.id;
            } else {
                editorTargetId = newSelectedIds.length === 1 ? newSelectedIds[0] : null;
            }

            return {
                nodes: state.nodes.map(n => ({ ...n, selected: newSelectedIds.includes(n.id) })),
                selectedNodeIds: newSelectedIds,
                selectedNodeId: editorTargetId,
                activeBlockId: state.isExecuting ? state.activeBlockId : (newSelectedIds.length === 1 ? newSelectedIds[0] : null)
            };
        });
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
            const flowNodes = (workflow.data?.nodes || []).map(node => {
                // Handle both formats:
                // 1. Template format: { id, type, position: { x, y }, data: {...} }
                // 2. Saved format: { id, x, y, type, name, ... } (flattened)

                if (node.position && node.data) {
                    // Template format - already in correct structure
                    return {
                        ...node,
                        type: 'custom', // Ensure correct ReactFlow type
                    };
                } else {
                    // Saved format - need to reconstruct
                    const { id, x, y, ...nodeData } = node;
                    return {
                        id,
                        type: 'custom',
                        position: { x: x || 0, y: y || 0 },
                        data: nodeData,
                    };
                }
            });

            const flowEdges = workflow.data?.edges || [];

            set({
                nodes: flowNodes,
                edges: flowEdges,
                currentProjectId: projectId,
                currentWorkflowId: workflowId
            });

            console.log('✅ Workflow loaded successfully:', { nodes: flowNodes.length, edges: flowEdges.length });
            
            // Auto-select React node if present
            const reactNode = flowNodes.find(n => n.data && (n.data.type === 'REACT' || n.data.block_type === 'REACT'));
            if (reactNode) {
                set({ selectedNodeId: reactNode.id });
            }
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
