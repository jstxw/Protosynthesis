import React, { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { useStore } from '../helpers/store';

const CustomNode = ({ data }) => {
  const { updateNode, updateInputValue, edges, togglePortVisibility, apiSchemas, removeBlock, activeBlockId } = useStore();

  const handleNameChange = (e) => {
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
    <div className="node-menu nodrag">
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
        {type === 'input' && <Handle type="target" position={Position.Left} id={port.key} />}
        
        <div className="port-label">
          <span>{port.key}</span>
          <span className="port-type">({port.data_type})</span>
        </div>

        {/* For unconnected inputs, show a manual input field */}
        {type === 'input' && !isConnected && (
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
        )}

        {type === 'output' && <Handle type="source" position={Position.Right} id={port.key} />}
      </div>
    );
  };

  const isActive = activeBlockId === data.id;

  return (
    <div className={`custom-node ${isActive ? 'active-block' : ''}`}>
      <div className="node-header">
        <input 
          type="text" 
          defaultValue={data.name} 
          onBlur={handleNameChange}
          className="nodrag node-name-input"
        />
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
              <option value="to_json">To JSON</option>
              <option value="params_to_json">Params to JSON</option>
              <option value="json_to_params">JSON to Params</option>
            </select>
            {(data.transformation_type === 'params_to_json' || data.transformation_type === 'json_to_params') && (
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