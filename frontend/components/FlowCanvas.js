import React, { useEffect, useMemo, useCallback } from 'react';
import ReactFlow, { Background, Controls, useReactFlow } from 'reactflow';
import 'reactflow/dist/style.css';
import { useStore } from '../helpers/store';
import CustomNode from './CustomNode';

const FlowCanvas = () => {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect, fetchGraph, fetchApiSchemas, toggleMenu, addBlock } = useStore();
  const { screenToFlowPosition } = useReactFlow();
  // Define our custom node type
  const nodeTypes = useMemo(() => ({ custom: CustomNode }), []);

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

      addBlock(data.type, { ...data.params, x: position.x, y: position.y });
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
      fitView
    >
      <Background />
      <Controls />
    </ReactFlow>
  );
};

export default FlowCanvas;