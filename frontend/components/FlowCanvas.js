import React, {useEffect, useMemo, useCallback} from 'react';
import ReactFlow, {Background, Controls, MiniMap, useReactFlow, ControlButton} from 'reactflow';
import 'reactflow/dist/style.css';
import {useStore} from '../helpers/store';
import CustomNode from './CustomNode';

const connectionLineStyle = { stroke: '#ffffff', strokeWidth: 3 };

const FlowCanvas = () => {
    const {
        nodes,
        edges,
        onNodesChange,
        onEdgesChange,
        onConnect,
        fetchApiSchemas,
        toggleMenu,
        addBlock,
        setHoveredNodeId,
        currentProjectId,
        currentWorkflowId,
        onSelectionChange,
        selectNode,
        shouldFitView,
        clearFitViewFlag,
        autoLayoutNodes,
        clearBoard
    } = useStore();
    const {screenToFlowPosition, fitView} = useReactFlow();
    // Define our custom node type
    const nodeTypes = useMemo(() => ({custom: CustomNode}), []);

    // Fetch API schemas when the component mounts
    useEffect(() => {
        fetchApiSchemas();
    }, [fetchApiSchemas]);

    // Fit view when auto-layout completes
    useEffect(() => {
        if (shouldFitView) {
            // Use a small delay to ensure nodes are rendered before fitting
            setTimeout(() => {
                fitView({ padding: 0.2, duration: 400 });
                clearFitViewFlag();
            }, 50);
        }
    }, [shouldFitView, fitView, clearFitViewFlag]);

    const handleNodeContextMenu = useCallback((event, node) => {
        event.preventDefault();
        toggleMenu(node.id);
    }, [toggleMenu]);

    const handleNodeClick = useCallback((event, node) => {
        // If user clicks on node, update selection in our store.
        // Support additive selection with ctrl/meta/shift key.
        const additive = event.ctrlKey || event.metaKey || event.shiftKey;
        selectNode(node.id, additive);
    }, [selectNode]);

    const onDragOver = useCallback((event) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }, []);

    const onDrop = useCallback(
        (event) => {
            event.preventDefault();

            const dataString = event.dataTransfer.getData('application/reactflow');
            if (!dataString) return;

            const data = JSON.parse(dataString);

            // Use screenToFlowPosition which is designed for this exact purpose.
            // It correctly translates screen coordinates to the flow's coordinate system.
            const position = screenToFlowPosition({
                x: event.clientX,
                y: event.clientY,
            });

            addBlock(data.type, {...data.params, x: position.x - 125, y: position.y});
        },
        [screenToFlowPosition, addBlock]
    );

    return (
        <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            onNodeContextMenu={handleNodeContextMenu}
            onNodeClick={handleNodeClick}
            onDrop={onDrop}
            onDragOver={onDragOver}
            onSelectionChange={onSelectionChange}
            onPaneClick={() => selectNode(null)}
            onNodeMouseEnter={(_, node) => setHoveredNodeId(node.id)}
            onNodeMouseLeave={() => setHoveredNodeId(null)}
            connectionLineType="smoothstep"
            connectionLineStyle={connectionLineStyle}
            snapToGrid={true}
            snapGrid={[25, 25]}
            defaultEdgeOptions={{ type: 'smoothstep', animated: false }}
            fitView
        >
            <Background id="grid-minor" variant="lines" gap={25} size={1} color="rgba(255, 255, 255, 0.05)" />
            <Background id="grid-major" variant="lines" gap={100} size={1} color="rgba(255, 255, 255, 0.15)" />
            <Controls showInteractive={false}>
                <ControlButton onClick={autoLayoutNodes} title="Auto-organize nodes">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <rect x="3" y="3" width="7" height="7" />
                        <rect x="14" y="3" width="7" height="7" />
                        <rect x="3" y="14" width="7" height="7" />
                        <rect x="14" y="14" width="7" height="7" />
                    </svg>
                </ControlButton>
                <ControlButton
                    onClick={() => {
                        if (window.confirm('Clear all nodes and connections from the board?')) {
                            clearBoard();
                        }
                    }}
                    title="Clear board"
                >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2" />
                        <line x1="10" y1="11" x2="10" y2="17" />
                        <line x1="14" y1="11" x2="14" y2="17" />
                    </svg>
                </ControlButton>
            </Controls>
            <MiniMap
                nodeColor={(node) => {
                    switch (node.data?.type) {
                        case 'START': return '#c5e1a5';
                        case 'REACT': return '#9fa8da';
                        case 'API': return '#f48fb1';
                        case 'STRING_BUILDER': return '#ffe082';
                        case 'LOGIC': return '#ffe082';
                        case 'TRANSFORM': return '#ffe082';
                        case 'WAIT': return '#ffe082';
                        case 'DIALOGUE': return '#ce93d8';
                        case 'API_KEY': return '#ffe082';
                        default: return '#D7CCC8';
                    }
                }}
                nodeStrokeWidth={3}
                zoomable
                pannable
                style={{
                    backgroundColor: 'var(--surface-color)',
                    border: '2px solid var(--border-color)',
                    borderRadius: '8px',
                    boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)'
                }}
            />
        </ReactFlow>
    );
};

export default FlowCanvas;