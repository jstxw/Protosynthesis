import React, {useEffect, useMemo, useCallback} from 'react';
import ReactFlow, {Background, Controls, useReactFlow} from 'reactflow';
import 'reactflow/dist/style.css';
import {useStore} from '../helpers/store';
import CustomNode from './CustomNode';

const connectionLineStyle = { stroke: '#ffffff', strokeWidth: 4, strokeDasharray: '10 8' };

const FlowCanvas = () => {
    const {
        nodes,
        edges,
        onNodesChange,
        onEdgesChange,
        onConnect,
        fetchGraph,
        fetchApiSchemas,
        toggleMenu,
        addBlock,
        setHoveredNodeId,
        onSelectionChange
    } = useStore();
    const {screenToFlowPosition} = useReactFlow();
    // Define our custom node type
    const nodeTypes = useMemo(() => ({custom: CustomNode}), []);

    // Fetch the initial graph state and schemas when the component mounts
    useEffect(() => {
        fetchGraph();
        fetchApiSchemas();
    }, [fetchGraph, fetchApiSchemas]);

    const handleNodeContextMenu = useCallback((event, node) => {
        event.preventDefault();
        toggleMenu(node.id);
    }, [toggleMenu]);

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
            onDrop={onDrop}
            onDragOver={onDragOver}
            onSelectionChange={onSelectionChange}
            onNodeMouseEnter={(_, node) => setHoveredNodeId(node.id)}
            onNodeMouseLeave={() => setHoveredNodeId(null)}
            connectionLineType="straight"
            connectionLineStyle={connectionLineStyle}
            fitView
        >
            <Background id="grid-minor" variant="lines" gap={25} size={1} color="rgba(255, 255, 255, 0.05)" />
            <Background id="grid-major" variant="lines" gap={100} size={1} color="rgba(255, 255, 255, 0.15)" />
            <Controls/>
        </ReactFlow>
    );
};

export default FlowCanvas;