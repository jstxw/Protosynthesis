import React, { memo, useState, useEffect } from 'react';
import { Handle, Position } from 'reactflow';
import { useStore } from '../helpers/store';
import Image from 'next/image';

const getIconForType = (type) => {
  switch (type) {
    case 'START': return '/play.svg';
    case 'REACT': return '/user.svg';
    case 'STRING_BUILDER': return '/text.svg';
    case 'LOGIC': return '/branch.svg';
    case 'TRANSFORM': return '/shuffle.svg';
    case 'WAIT': return '/clock.svg';
    case 'LOOP': return '/loop.svg';
    case 'API': return '/window.svg';
    case 'DIALOGUE': return '/chat.svg';
    default: return null;
  }
};

const CustomNode = ({ data }) => {
  const { updateNode, updateInputValue, updateOutputValue, edges, togglePortVisibility, apiSchemas, removeBlock, activeBlockId } = useStore();
  const [name, setName] = useState(data.name || '');

  useEffect(() => {
    setName(data.name || '');
  }, [data.name]);

  const handleNameBlur = (e) => {
    updateNode(data.id, { name: e.target.value });
  };

  const handleTemplateChange = (e) => {
    updateNode(data.id, { template: e.target.value });
  };

  const handleTransformTypeChange = (e) => {
    updateNode(data.id, { transformation_type: e.target.value });
  };

  const handleLogicOperationChange = (e) => {
    updateNode(data.id, { operation: e.target.value });
  };

  const handleFieldsChange = (e) => {
    updateNode(data.id, { fields: e.target.value });
  };

  const handleDelayChange = (e) => {
    updateNode(data.id, { delay: e.target.value });
  };

  // The menu component, rendered conditionally
  const SettingsMenu = () => (
 <div className="node-menu nodrag" onWheel={(e) => e.stopPropagation()}>
      {/* API Block Specific Settings */}
      {data.type === 'API' && (
        <div className="menu-section">
          <label>API Schema</label>
          <select
            value={data.schema_key}
            onChange={(e) => updateNode(data.id, { schema_key: e.target.value })}
          >
            {Object.entries(apiSchemas).map(([key, schema]) => (
              <option key={key} value={key}>{schema.name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Port Visibility Settings */}
      <div className="menu-section">
        <label>Visible Inputs</label>
        {data.inputs.map(port => (
          <div key={`vis-in-${port.key}`} className="menu-item">
            <input
              type="checkbox"
              id={`vis-in-${data.id}-${port.key}`}
              checked={!data.hidden_inputs?.includes(port.key)}
              onChange={() => togglePortVisibility(data.id, port.key, 'input')}
            />
            <label htmlFor={`vis-in-${data.id}-${port.key}`}>{port.key}</label>
          </div>
        ))}
      </div>
      <div className="menu-section">
        <label>Visible Outputs</label>
        {data.outputs.map(port => (
          <div key={`vis-out-${port.key}`} className="menu-item">
            <input
              type="checkbox"
              id={`vis-out-${data.id}-${port.key}`}
              checked={!data.hidden_outputs?.includes(port.key)}
              onChange={() => togglePortVisibility(data.id, port.key, 'output')}
            />
            <label htmlFor={`vis-out-${data.id}-${port.key}`} style={{ flexGrow: 1 }}>{port.key}</label>
            {port.value !== undefined && port.value !== null && (
              <span className="port-value-compact" title={typeof port.value === 'object' ? JSON.stringify(port.value, null, 2) : String(port.value)}>
                {typeof port.value === 'object' ? JSON.stringify(port.value) : String(port.value)}
              </span>
            )}
          </div>
        ))}
      </div>
    </div>
  );

  // This is the crucial part: render the key, not the object.
  const renderPort = (port, type) => {
    const isConnected = edges.some(edge => 
      (type === 'input' && edge.target === data.id && edge.targetHandle === port.key) ||
      (type === 'output' && edge.source === data.id && edge.sourceHandle === port.key)
    );

    return (
      <div key={port.key} className="port">
        {type === 'input' && <Handle type="target" position={Position.Left} id={port.key} className={isConnected ? 'handle-connected' : ''} />}
        
        <div className="port-label">
          <span>{port.key}</span>
          <span className="port-type">({port.data_type})</span>
        </div>

        {/* For unconnected inputs, show a manual input field */}
        {type === 'input' && !isConnected && (
          port.data_type === 'boolean' ? (
            <input
              type="checkbox"
              className="nodrag"
              checked={!!port.value}
              onChange={(e) => updateInputValue(data.id, port.key, e.target.checked)}
              style={{ width: 'auto', margin: '0 5px' }}
            />
          ) : (
            <input
              type="text"
              className="nodrag" // Prevents node dragging when interacting with the input
              defaultValue={
                typeof port.value === 'object' && port.value !== null
                  ? JSON.stringify(port.value)
                  : port.value || ''
              }
              onChange={(e) => updateInputValue(data.id, port.key, e.target.value)}
              placeholder="Manual Input"
            />
          )
        )}

        {type === 'output' && <Handle type="source" position={Position.Right} id={port.key} className={isConnected ? 'handle-connected' : ''} />}
      </div>
    );
  };

  const isActive = activeBlockId === data.id;

  const getHeaderClass = () => {
    switch (data.type) {
      case 'API': return 'node-header-api';
      case 'START': return 'node-header-start';
      case 'REACT': return 'node-header-react';
      case 'STRING_BUILDER': return 'node-header-string';
      case 'LOGIC': return 'node-header-logic';
      case 'TRANSFORM': return 'node-header-transform';
      case 'WAIT': return 'node-header-wait';
      case 'LOOP': return 'node-header-logic'; // Reuse logic color
      case 'DIALOGUE': return 'node-header-dialogue';
      default: return '';
    }
  };

  return (
    <div className={`custom-node ${isActive ? 'active-block' : ''}`}>
      {getIconForType(data.type) && (
        <div className={`node-icon-nub ${getHeaderClass()}`}>
          <Image 
            src={getIconForType(data.type)} 
            width={28} 
            height={28} 
            alt="" 
            className="node-nub-icon" 
          />
        </div>
      )}
      <div className={`node-header ${getHeaderClass()}`}>
        <div style={{ display: 'grid', marginRight: 'auto' }}>
          <span style={{ 
            gridArea: '1/1', 
            visibility: 'hidden', 
            whiteSpace: 'pre', 
            fontWeight: 'bold', 
            fontFamily: 'inherit',
            minWidth: '20px'
          }}>
            {name || ' '}
          </span>
          <input 
            type="text" 
            value={name} 
            onChange={(e) => setName(e.target.value)}
            onBlur={handleNameBlur}
            className="nodrag node-name-input"
            style={{ gridArea: '1/1', width: '100%', minWidth: '0', padding: 0 }}
          />
        </div>
        {data.menu_open ? (
          <button className="delete-button nodrag" onClick={() => removeBlock(data.id)} title="Delete Block">
            &times;
          </button>
        ) : (
          <span className="node-type">{data.type}</span>
        )}
      </div>

      <div className="node-body">
        <div className="node-ports">
          <div className="port-column">
            <div className="port-title">Inputs</div>
            {data.inputs
              .filter(input => !data.hidden_inputs?.includes(input.key))
              .map(input => renderPort(input, 'input'))}
          </div>
          <div className="port-column">
            <div className="port-title">Outputs</div>
            {data.outputs
              .filter(output => !data.hidden_outputs?.includes(output.key))
              .map(output => renderPort(output, 'output'))}
          </div>
        </div>

        {/* Render special controls for specific block types */}
        {data.type === 'STRING_BUILDER' && (
          <div className="node-config">
            <label>Template</label>
            <textarea
              className="nodrag"
              defaultValue={data.template}
              onBlur={handleTemplateChange}
              rows={3}
            />
          </div>
        )}

        {data.type === 'TRANSFORM' && (
          <div className="node-config">
            <label>Type</label>
            <select 
              className="nodrag"
              value={data.transformation_type}
              onChange={handleTransformTypeChange}
              style={{ width: '100%', marginBottom: '5px' }}
            >
              <option value="to_string">To String</option>
              <option value="to_string">Get Key from JSON</option>
              <option value="to_json">To JSON</option>
              <option value="params_to_json">Params to JSON</option>
            </select>
            {data.transformation_type === 'params_to_json' && (
              <>
                <label>Fields (comma separated)</label>
                <input 
                  type="text"
                  className="nodrag"
                  defaultValue={data.fields}
                  onBlur={handleFieldsChange}
                  placeholder="e.g. name, age"
                  style={{ width: '100%' }}
                />
              </>
            )}
          </div>
        )}

        {data.type === 'LOGIC' && (
          <div className="node-config">
            <label>Operation</label>
            <select 
              className="nodrag"
              value={data.operation}
              onChange={handleLogicOperationChange}
              style={{ width: '100%', marginBottom: '5px' }}
            >
              <option value="add">Add (+)</option>
              <option value="subtract">Subtract (-)</option>
              <option value="multiply">Multiply (*)</option>
              <option value="divide">Divide (/)</option>
              <option value="equals">Equals (==)</option>
              <option value="not_equals">Not Equals (!=)</option>
              <option value="greater_than">Greater Than (&gt;)</option>
              <option value="less_than">Less Than (&lt;)</option>
              <option value="and">AND</option>
              <option value="or">OR</option>
            </select>
          </div>
        )}

        {data.type === 'WAIT' && (
          <div className="node-config">
            <label>Delay (seconds)</label>
            <input 
              type="number"
              className="nodrag"
              defaultValue={data.delay}
              onBlur={handleDelayChange}
              style={{ width: '100%' }}
            />
          </div>
        )}

      </div>

      {data.menu_open && <SettingsMenu />}
    </div>
  );
};

export default memo(CustomNode);