import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useStore } from '../helpers/store';
import { workflowService } from '../services/projects';
import Image from 'next/image';

const ControlPanel = () => {
  const router = useRouter();
  const { addBlock, apiSchemas, executeGraph, saveProject, loadProject, currentProjectId, currentWorkflowId, selectNode } = useStore();
  // Whether a React I/O node already exists in the current graph
  const reactExists = useStore(state => (state.nodes || []).some(n => (n.data && (n.data.type === 'REACT' || n.data.block_type === 'REACT'))));
  const existingReactNodeId = useStore(state => {
    const n = (state.nodes || []).find(x => x.data && (x.data.type === 'REACT' || x.data.block_type === 'REACT'));
    return n ? n.id : null;
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [workflows, setWorkflows] = useState([]);
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (currentProjectId) {
      workflowService.getAllWorkflows(currentProjectId)
        .then(setWorkflows)
        .catch(console.error);
    }
  }, [currentProjectId]);

  const onDragStart = (event, blockData) => {
    const dataString = JSON.stringify(blockData);
    event.dataTransfer.setData('application/reactflow', dataString);
    event.dataTransfer.effectAllowed = 'move';
  };

  const handleLoadClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const projectData = JSON.parse(e.target.result);
        loadProject(projectData);
      } catch (error) {
        console.error("Error parsing project file:", error);
        alert("Invalid project file. Please select a valid JSON file.");
      }
    };
    reader.readAsText(file);
  };

  const logicBlockTypes = [
    { type: 'START', name: 'Start', description: 'Begins a flow execution.', icon: '/play.svg' },
    { type: 'REACT', name: 'React I/O', description: 'Interface with the UI.', icon: '/user.svg' },
    { type: 'DIALOGUE', name: 'Dialogue', description: 'Input and Output display.', icon: '/chat.svg' },
    { type: 'STRING_BUILDER', name: 'String Builder', description: 'Formats text with variables.', icon: '/text.svg' },
    { type: 'LOGIC', name: 'Logic', description: 'Performs conditional logic.', icon: '/branch.svg' },
    { type: 'API_KEY', name: 'API Key', description: 'Stores and provides an API key.', icon: '/key.svg' },
    { type: 'TRANSFORM', name: 'Transform', description: 'Modifies data formats.', icon: '/shuffle.svg' },
    { type: 'WAIT', name: 'Wait', description: 'Pauses execution.', icon: '/clock.svg' },
  ];

  const filteredApiSchemas = Object.entries(apiSchemas)
    .filter(([, schema]) =>
      schema.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

  return (
    <aside className="control-panel" onDrop={(e) => e.preventDefault()}>
      <div className="panel-header-buttons">
        <button onClick={() => router.push('/')} title="Back to Dashboard">
          <Image src="/arrow-left.svg" alt="Back" width={20} height={20} />
        </button>
        <button onClick={saveProject} title="Save Project">
          <Image src="/save.svg" alt="Save" width={20} height={20} />
        </button>
        <button onClick={handleLoadClick} title="Load Project">
          <Image src="/load.svg" alt="Load" width={20} height={20} />
        </button>
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleFileChange}
          accept=".json,application/json"
        />
        <button onClick={executeGraph} className="execute-button" title="Run Graph">
          <Image src="/play.svg" alt="Run" width={20} height={20} />
        </button>
      </div>

      {currentProjectId && (
        <div className="controls-section">
          <h4>Workflows</h4>
          <div className="block-list">
            {workflows.map(wf => (
              <div
                key={wf.workflow_id}
                className={`block-list-item ${currentWorkflowId === wf.workflow_id ? 'active' : ''}`}
                onClick={() => router.push(`/workflow?project=${currentProjectId}&workflow=${wf.workflow_id}`)}
                title={wf.name}
              >
                <Image src="/branch.svg" alt="Workflow" width={18} height={18} className="block-list-item-icon" />
                <div className="block-list-item-content">
                  <div className="block-list-item-name">{wf.name}</div>
                  <div className="block-list-item-desc">
                    {new Date(wf.updated_at || wf.created_at).toLocaleDateString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="controls-section">
        <h4>Logic Blocks</h4>
        <div className="logic-grid" onWheel={(e) => e.stopPropagation()}>
          {logicBlockTypes.map(block => (
            <div
              key={block.type}
              className={`block-list-item ${block.type === 'REACT' && reactExists ? 'disabled' : ''}`}
              onClick={() => {
                if (block.type === 'REACT' && reactExists) {
                  // If a React node exists, select it in the canvas so the user can jump to it
                  if (existingReactNodeId) {
                    selectNode(existingReactNodeId, false);
                  }
                  return;
                }
                addBlock(block.type, { name: block.name });
              }}
              onDragStart={(event) => {
                if (block.type === 'REACT' && reactExists) { event.preventDefault(); return; }
                onDragStart(event, { type: block.type, params: { name: block.name } });
              }}
              draggable={!(block.type === 'REACT' && reactExists)}
              title={block.type === 'REACT' && reactExists ? 'React I/O (only one allowed)' : `Add ${block.name} block`}
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
          <div className="block-list api-list" onWheel={(e) => e.stopPropagation()}>
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
