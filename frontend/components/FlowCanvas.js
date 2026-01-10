import React, { useEffect, useMemo, useCallback } from 'react';
import ReactFlow, { Background, Controls, useReactFlow } from 'reactflow';
import 'reactflow/dist/style.css';
import { useStore } from '../lib/store';
import CustomNode from './CustomNode';

const FlowCanvas = () => {
  const { nodes, edges, onNodesChange, onEdgesChange, onConnect, fetchGraph, fetchApiSchemas, openContextMenu, closeContextMenu, addBlock } = useStore();
  const { project } = useReactFlow();
  // Define our custom node type
  const nodeTypes = useMemo(() => ({ custom: CustomNode }), []);

  // Fetch the initial graph state and schemas when the component mounts
  useEffect(() => {
    fetchGraph();
    fetchApiSchemas();
  }, [fetchGraph, fetchApiSchemas]);

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback((event) => {
    event.preventDefault();

    const dataString = event.dataTransfer.getData('application/reactflow');
    
    if (!dataString) return;

    const data = JSON.parse(dataString);

    // The `project` function provided by useReactFlow already handles
    // converting viewport coordinates (event.clientX) to flow coordinates.
    // No manual offset calculation is needed. This is the fix.
    const position = project({
      x: event.clientX,
      y: event.clientY,
    });

    addBlock(data.type, { ...data.params, x: position.x, y: position.y });
  }, [project, addBlock]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onConnect={onConnect}
      nodeTypes={nodeTypes}
      onNodeContextMenu={openContextMenu}
      onPaneClick={closeContextMenu}
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