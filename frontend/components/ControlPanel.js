import React, { useState, useRef } from 'react';
import { useStore } from '../helpers/store';
import Image from 'next/image';

const ControlPanel = () => {
  const { addBlock, apiSchemas } = useStore();
  const [searchTerm, setSearchTerm] = useState('');

  const onDragStart = (event, blockData) => {
    const dataString = JSON.stringify(blockData);
    event.dataTransfer.setData('application/reactflow', dataString);
    event.dataTransfer.effectAllowed = 'move';
  };

  const logicBlockTypes = [
    { type: 'START', name: 'Start', description: 'Begins a flow execution.', icon: '/play.svg' },
    { type: 'REACT', name: 'React I/O', description: 'Interface with the UI.', icon: '/user.svg' },
    { type: 'STRING_BUILDER', name: 'String Builder', description: 'Formats text with variables.', icon: '/text.svg' },
    { type: 'LOGIC', name: 'Logic', description: 'Performs conditional logic.', icon: '/branch.svg' },
    { type: 'TRANSFORM', name: 'Transform', description: 'Modifies data formats.', icon: '/shuffle.svg' },
    { type: 'WAIT', name: 'Wait', description: 'Pauses execution.', icon: '/clock.svg' },
  ];

  const filteredApiSchemas = Object.entries(apiSchemas)
    .filter(([key, schema]) => 
      schema.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

  return (
    <aside className="control-panel" onDrop={(e) => e.preventDefault()}>
      <h3>Blocks</h3>
      <div className="controls-section">
        <h4>Logic Blocks</h4>
        <div className="block-list">
          {logicBlockTypes.map(block => (
            <div 
              key={block.type} 
              className="block-list-item" 
              onClick={() => addBlock(block.type, { name: block.name })} 
              onDragStart={(event) => onDragStart(event, { type: block.type, params: { name: block.name } })}
              draggable
              title={`Add ${block.name} block`}
            >
              <Image src={block.icon} alt={`${block.name} icon`} width={18} height={18} className="block-list-item-icon" />
              <div className="block-list-item-content">
                <div className="block-list-item-name">{block.name}</div>
                <div className="block-list-item-desc">{block.description}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className="controls-section">
        <h4>API Library</h4>
        <input
          type="text"
          placeholder="Search APIs..."
          className="search-input"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <div className="block-list api-list">
          {filteredApiSchemas.map(([key, schema]) => (
            <div 
              key={key} 
              className="block-list-item" 
              onClick={() => addBlock('API', { schema_key: key, name: schema.name })} 
              onDragStart={(event) => onDragStart(event, { type: 'API', params: { schema_key: key, name: schema.name } })}
              draggable
              title={`Add ${schema.name} block`}
            >
              <Image src="/window.svg" alt="API icon" width={18} height={18} className="block-list-item-icon" />
              <div className="block-list-item-content">
                <div className="block-list-item-name">{schema.name}</div>
                <div className="block-list-item-desc">{schema.doc_url}</div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
};

export default ControlPanel;