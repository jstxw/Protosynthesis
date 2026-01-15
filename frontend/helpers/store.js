import {create} from 'zustand';
import axios from 'axios';
import {
    applyNodeChanges,
    applyEdgeChanges,
    addEdge,
} from 'reactflow';
import { apiClient } from '../services/api';

const API_URL = 'http://localhost:5001/api';

// Helper to generate unique IDs
const generateId = () => `block_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

// Helper to initialize block data locally (no backend call needed)
const initializeBlockData = (type, params = {}) => {
    const id = generateId();
    const baseBlock = {
        id,
        name: params.name || `New ${type} Block`,
        block_type: type,
        type, // Ensure both are set
        x: params.x || 150,
        y: params.y || 150,
        inputs: {},
        outputs: {},
        input_meta: {},
        output_meta: {},
        visible_inputs: [],
        visible_outputs: [],
        is_collapsed: false,
        menu_open: false,
    };

    // Type-specific initialization
    switch (type) {
        case 'START':
            return {
                ...baseBlock,
                outputs: { result: null },
                output_meta: { result: { type: 'any', label: 'Start' } },
                visible_outputs: ['result'],
            };
        case 'API':
            return {
                ...baseBlock,
                url: params.url || '',
                method: params.method || 'GET',
                schema_key: params.schema_key || 'custom',
                inputs: { headers: {}, body: '' },
                outputs: { response: null },
                input_meta: {
                    headers: { type: 'object', label: 'Headers' },
                    body: { type: 'string', label: 'Body' }
                },
                output_meta: { response: { type: 'object', label: 'Response' } },
                visible_inputs: ['headers', 'body'],
                visible_outputs: ['response'],
            };
        case 'LOGIC':
            return {
                ...baseBlock,
                operation: params.operation || 'add',
                inputs: { a: null, b: null },
                outputs: { result: null },
                input_meta: {
                    a: { type: 'number', label: 'A' },
                    b: { type: 'number', label: 'B' }
                },
                output_meta: { result: { type: 'number', label: 'Result' } },
                visible_inputs: ['a', 'b'],
                visible_outputs: ['result'],
            };
        case 'TRANSFORM':
            return {
                ...baseBlock,
                transformation_type: params.transformation_type || 'to_string',
                fields: params.fields || '',
                inputs: { input: null },
                outputs: { output: null },
                input_meta: { input: { type: 'any', label: 'Input' } },
                output_meta: { output: { type: 'any', label: 'Output' } },
                visible_inputs: ['input'],
                visible_outputs: ['output'],
            };
        case 'REACT':
            return {
                ...baseBlock,
                jsx_code: params.jsx_code || 'export default function Component() { return <div>Hello</div>; }',
                css_code: params.css_code || '',
                inputs: {},
                outputs: {},
                input_meta: {},
                output_meta: {},
                visible_inputs: [],
                visible_outputs: [],
            };
        case 'STRING_BUILDER':
            return {
                ...baseBlock,
                template: params.template || '',
                inputs: {},
                outputs: { result: null },
                input_meta: {},
                output_meta: { result: { type: 'string', label: 'Result' } },
                visible_inputs: [],
                visible_outputs: ['result'],
            };
        case 'WAIT':
            return {
                ...baseBlock,
                delay: params.delay || 1.0,
                inputs: { input: null },
                outputs: { output: null },
                input_meta: { input: { type: 'any', label: 'Input' } },
                output_meta: { output: { type: 'any', label: 'Output' } },
                visible_inputs: ['input'],
                visible_outputs: ['output'],
            };
        case 'DIALOGUE':
            return {
                ...baseBlock,
                message: params.message || '',
                inputs: {},
                outputs: { response: null },
                input_meta: {},
                output_meta: { response: { type: 'string', label: 'Response' } },
                visible_inputs: [],
                visible_outputs: ['response'],
            };
        case 'API_KEY':
            return {
                ...baseBlock,
                selected_key: params.selected_key || '',
                inputs: {},
                outputs: { api_key: null },
                input_meta: {},
                output_meta: { api_key: { type: 'string', label: 'API Key' } },
                visible_inputs: [],
                visible_outputs: ['api_key'],
            };
        default:
            return baseBlock;
    }
};

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

    // Removed fetchGraph - use loadWorkflowFromV2 instead

    // --- REACT FLOW HANDLERS ---
    onNodesChange: (changes) => {
        set({
            nodes: applyNodeChanges(changes, get().nodes),
        });

        // Trigger auto-save for position changes in V2 mode
        changes.forEach(change => {
            if (change.type === 'position' && change.dragging === false) {
                const { currentProjectId, currentWorkflowId } = get();
                if (currentProjectId && currentWorkflowId) {
                    get().scheduleAutoSave();
                }
            }
        });
    },

    onEdgesChange: (changes) => {
        set({
            edges: applyEdgeChanges(changes, get().edges),
        });

        // Trigger auto-save for edge changes in V2 mode
        const { currentProjectId, currentWorkflowId } = get();
        if (currentProjectId && currentWorkflowId && changes.length > 0) {
            get().scheduleAutoSave();
        }
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

        // Trigger auto-save for V2 workflows
        const { currentProjectId, currentWorkflowId } = get();
        if (currentProjectId && currentWorkflowId) {
            get().scheduleAutoSave();
        }
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

        try {
            // Helper function to normalize ports
            const normalizePortsToArray = (portsData, metaData) => {
                if (Array.isArray(portsData)) return portsData;
                if (typeof portsData === 'object' && portsData !== null) {
                    return Object.entries(portsData).map(([key, value]) => ({
                        key,
                        value,
                        data_type: metaData?.[key]?.type || 'any'
                    }));
                }
                return [];
            };

            // Create block locally (no backend call needed)
            const initializedBlock = initializeBlockData(type, params);
            const flowNode = createFlowNode(initializedBlock);

            // Normalize inputs/outputs to array format (create new object, don't mutate)
            const normalizedNode = {
                ...flowNode,
                data: {
                    ...flowNode.data,
                    inputs: normalizePortsToArray(flowNode.data.inputs, flowNode.data.input_meta),
                    outputs: normalizePortsToArray(flowNode.data.outputs, flowNode.data.output_meta)
                }
            };

            console.log("Adding block locally:", normalizedNode);
            set(state => ({nodes: [...state.nodes, normalizedNode]}));
            get().selectNode(normalizedNode.id);

            // Auto-save if in V2 mode
            if (currentProjectId && currentWorkflowId) {
                get().scheduleAutoSave();
            }
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

        // Trigger auto-save in V2 mode
        if (currentProjectId && currentWorkflowId) {
            get().scheduleAutoSave();
        }
    },

    updateInputValue: async (nodeId, inputKey, value) => {
        const { currentProjectId, currentWorkflowId } = get();

        // Optimistic update
        set(state => ({
            nodes: state.nodes.map(node => {
                if (node.id === nodeId) {
                    // Handle both array and object format
                    let newInputs;
                    if (Array.isArray(node.data.inputs)) {
                        newInputs = node.data.inputs.map(input =>
                            input.key === inputKey ? { ...input, value } : input
                        );
                    } else {
                        newInputs = {...(node.data.inputs || {}), [inputKey]: value};
                    }
                    return {...node, data: {...node.data, inputs: newInputs}};
                }
                return node;
            })
        }));

        // Trigger auto-save in V2 mode
        if (currentProjectId && currentWorkflowId) {
            get().scheduleAutoSave();
        }
    },

    updateOutputValue: async (nodeId, outputKey, value) => {
        const { currentProjectId, currentWorkflowId } = get();

        // Update the local state
        set(state => ({
            nodes: state.nodes.map(node => {
                if (node.id === nodeId) {
                    // Handle both array and object format
                    let newOutputs;
                    if (Array.isArray(node.data.outputs)) {
                        newOutputs = node.data.outputs.map(output =>
                            output.key === outputKey ? { ...output, value } : output
                        );
                    } else {
                        newOutputs = {...(node.data.outputs || {}), [outputKey]: value};
                    }
                    return { ...node, data: { ...node.data, outputs: newOutputs } };
                }
                return node;
            })
        }));

        // Trigger auto-save in V2 mode
        if (currentProjectId && currentWorkflowId) {
            get().scheduleAutoSave();
        }
    },

    removeBlock: async (nodeId) => {
        const { currentProjectId, currentWorkflowId } = get();

        // Optimistic removal
        set(state => ({
            nodes: state.nodes.filter(n => n.id !== nodeId),
            edges: state.edges.filter(e => e.source !== nodeId && e.target !== nodeId),
        }));

        // Trigger auto-save in V2 mode
        if (currentProjectId && currentWorkflowId) {
            get().scheduleAutoSave();
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
            // Auto-save in V2 mode (menu state persisted)
            const { currentProjectId, currentWorkflowId } = get();
            if (currentProjectId && currentWorkflowId) {
                get().scheduleAutoSave();
            }
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

        // Auto-save in V2 mode
        const { currentProjectId, currentWorkflowId } = get();
        if (currentProjectId && currentWorkflowId) {
            get().scheduleAutoSave();
        }
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
        // Auto-save in V2 mode
        const { currentProjectId, currentWorkflowId } = get();
        if (currentProjectId && currentWorkflowId) {
            get().scheduleAutoSave();
        }
    },

    // --- EXECUTION ---
    // Legacy executeGraph removed - use executeWorkflowV2 instead
    executeGraph: async () => {
        console.warn('executeGraph (legacy) is deprecated. Use executeWorkflowV2 instead.');
        alert('Please use the Execute button with a project/workflow ID loaded.');
    },

    executeGraphLegacy: async () => {
        // DEPRECATED: This function used /api/execute which has been removed
        set({ isExecuting: true, executionLogs: ["Starting execution..."], activeBlockId: null, executionResult: null });

        try {
            // This endpoint no longer exists
            const response = await fetch(`${API_URL}/execute_REMOVED`, {
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
    // DEPRECATED: Use saveWorkflowToV2 and loadWorkflowFromV2 instead
    saveProject: async () => {
        console.warn('saveProject (legacy) is deprecated. Workflows are auto-saved in V2 mode.');
        alert('Workflows are automatically saved. No manual save needed.');
    },

    // DEPRECATED: Use loadWorkflowFromV2 instead
    loadProject: async (projectData) => {
        console.warn('loadProject (legacy) is deprecated. Use loadWorkflowFromV2 instead.');
        alert('Please open a workflow from the dashboard.');
        /* Legacy code removed - used /api/project/load endpoint which no longer exists */
    },

    // --- NEW V2 API WORKFLOW MANAGEMENT ---
    setCurrentWorkflow: (projectId, workflowId) => {
        set({ currentProjectId: projectId, currentWorkflowId: workflowId });
    },

    // Helper to normalize inputs/outputs to array format
    normalizePortsToArray: (portsData, metaData) => {
        if (Array.isArray(portsData)) return portsData;
        if (typeof portsData === 'object' && portsData !== null) {
            return Object.entries(portsData).map(([key, value]) => ({
                key,
                value,
                data_type: metaData?.[key]?.type || 'any'
            }));
        }
        return [];
    },

    loadWorkflowFromV2: async (projectId, workflowId) => {
        try {
            console.log(`Loading workflow ${workflowId} from project ${projectId}`);
            const response = await apiClient.get(`/v2/projects/${projectId}/workflows/${workflowId}`);
            const workflow = response.data;

            // Helper function to normalize ports (defined locally to avoid store getter issues)
            const normalizePortsToArray = (portsData, metaData) => {
                if (Array.isArray(portsData)) return portsData;
                if (typeof portsData === 'object' && portsData !== null) {
                    return Object.entries(portsData).map(([key, value]) => ({
                        key,
                        value,
                        data_type: metaData?.[key]?.type || 'any'
                    }));
                }
                return [];
            };

            // Convert workflow data to ReactFlow format
            const flowNodes = (workflow.data?.nodes || []).map(node => {
                // Handle both formats:
                // 1. Template format: { id, type, position: { x, y }, data: {...} }
                // 2. Saved format: { id, x, y, type, name, ... } (flattened)

                console.log('Loading node:', node);

                let resultNode;
                if (node.position && node.data) {
                    // Template format - already in correct structure
                    console.log('Template format - data.inputs:', node.data.inputs);

                    // Normalize inputs/outputs and create new data object
                    const normalizedInputs = normalizePortsToArray(node.data.inputs, node.data.input_meta);
                    const normalizedOutputs = normalizePortsToArray(node.data.outputs, node.data.output_meta);

                    resultNode = {
                        id: node.id,
                        type: 'custom',
                        position: node.position,
                        data: {
                            ...node.data,
                            inputs: normalizedInputs,
                            outputs: normalizedOutputs,
                            hidden_inputs: node.data.hidden_inputs || [],
                            hidden_outputs: node.data.hidden_outputs || []
                        }
                    };
                } else {
                    // Saved format - need to reconstruct
                    const { id, x, y, ...nodeData } = node;
                    console.log('Saved format - nodeData:', nodeData);

                    // Normalize inputs/outputs and create new data object
                    const normalizedInputs = normalizePortsToArray(nodeData.inputs, nodeData.input_meta);
                    const normalizedOutputs = normalizePortsToArray(nodeData.outputs, nodeData.output_meta);

                    resultNode = {
                        id,
                        type: 'custom',
                        position: { x: x || 0, y: y || 0 },
                        data: {
                            ...nodeData,
                            inputs: normalizedInputs,
                            outputs: normalizedOutputs
                        },
                    };
                }

                return resultNode;
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
        const { nodes, edges, currentProjectId, currentWorkflowId, autoSaveTimer } = get();

        if (!currentProjectId || !currentWorkflowId) {
            console.error("Cannot save: missing project or workflow ID");
            return;
        }

        // Clear existing timer
        if (autoSaveTimer) {
            clearTimeout(autoSaveTimer);
            set({ autoSaveTimer: null });
        }

        try {
            // Actually save to backend using the API client
            await apiClient.put(
                `/v2/projects/${currentProjectId}/workflows/${currentWorkflowId}`,
                {
                    data: {
                        nodes: nodes,
                        edges: edges
                    }
                }
            );

            console.log("Workflow saved successfully");

        } catch (error) {
            console.error("Error saving workflow:", error);
            // Don't throw - allow user to continue working
        }
    },

    scheduleAutoSave: () => {
        const { autoSaveTimer } = get();

        // Clear existing timer
        if (autoSaveTimer) {
            clearTimeout(autoSaveTimer);
        }

        // Schedule save after 2 seconds of inactivity
        const timer = setTimeout(() => {
            get().saveWorkflowToV2();
        }, 2000);

        set({ autoSaveTimer: timer });
    },
}));
