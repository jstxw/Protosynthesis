import { useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { useStore } from '../helpers/store';
import Image from 'next/image';

const ControlPanel = () => {
  const router = useRouter();
  const { addBlock, apiSchemas, executeGraph, saveProject, loadProject, selectNode } = useStore();
  // Whether a React I/O node already exists in the current graph
  const reactExists = useStore(state => (state.nodes || []).some(n => (n.data && (n.data.type === 'REACT' || n.data.block_type === 'REACT'))));
  const existingReactNodeId = useStore(state => {
    const n = (state.nodes || []).find(x => x.data && (x.data.type === 'REACT' || x.data.block_type === 'REACT'));
    return n ? n.id : null;
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCategories, setExpandedCategories] = useState({
    ai: true,
    communication: true,
    payment: true,
    productivity: true,
    data: true,
    fun: true,
    utility: true,
    other: true
  });
  const fileInputRef = useRef(null);

  const toggleCategory = (category) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }));
  };

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

  // Group APIs by category
  const groupedApis = filteredApiSchemas.reduce((groups, [key, schema]) => {
    const category = schema.category || 'other';
    if (!groups[category]) {
      groups[category] = [];
    }
    groups[category].push([key, schema]);
    return groups;
  }, {});

  // Category display names and order
  const categoryInfo = {
    ai: { name: 'AI & ML' },
    communication: { name: 'Communication' },
    payment: { name: 'Payments' },
    productivity: { name: 'Productivity' },
    data: { name: 'Data & Storage' },
    fun: { name: 'Fun & Utility' },
    utility: { name: 'Utility' },
    other: { name: 'Other' }
  };

  const categoryOrder = ['ai', 'communication', 'payment', 'productivity', 'data', 'fun', 'utility', 'other'];

  // Auth icon helper
  const getAuthIcon = (authType) => {
    if (!authType || authType === 'none') return null;
    return '🔒';
  };

  // Generate a consistent color based on the API name
  const getApiColor = (name) => {
    const colors = [
      '#f48fb1', // pink (API)
      '#9fa8da', // blue (React)
      '#c5e1a5', // green (Start)
      '#ffe082', // yellow (Logic)
      '#ce93d8', // purple (Dialogue)
      '#81c784', // green2
      '#64b5f6', // blue2
      '#ffb74d', // orange
      '#e57373', // red
      '#4db6ac', // teal
    ];

    // Simple hash function to pick a consistent color
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
  };

  // Map API keys to logo URLs or icon info
  const getLogoInfo = (key) => {
    const logoMap = {
      'openai_chat': 'https://cdn.simpleicons.org/openai/white',
      'anthropic_claude': 'https://cdn.simpleicons.org/anthropic/white',
      'google_gemini': 'https://cdn.simpleicons.org/google/white',
      'google_maps_geocode': 'https://cdn.simpleicons.org/googlemaps/white',
      'google_sheets': 'https://cdn.simpleicons.org/googlesheets/white',
      'google_calendar': 'https://cdn.simpleicons.org/googlecalendar/white',
      'stripe_charge': 'https://cdn.simpleicons.org/stripe/white',
      'paypal_payment': 'https://cdn.simpleicons.org/paypal/white',
      'slack_webhook': 'https://cdn.simpleicons.org/slack/white',
      'discord_webhook': 'https://cdn.simpleicons.org/discord/white',
      'telegram_bot': 'https://cdn.simpleicons.org/telegram/white',
      'twilio_send_sms': 'https://cdn.simpleicons.org/twilio/white',
      'notion_page': 'https://cdn.simpleicons.org/notion/white',
      'airtable_list': 'https://cdn.simpleicons.org/airtable/white',
      'mongodb_find': 'https://cdn.simpleicons.org/mongodb/white',
      'todoist': 'https://cdn.simpleicons.org/todoist/white',
      'stability_ai': 'https://cdn.simpleicons.org/stablediffusion/white',
      'huggingface': 'https://cdn.simpleicons.org/huggingface/white',
    };

    return logoMap[key] || null;
  };

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

      <div className="controls-section api-library-section">
        <h4>API Library</h4>
        <input
          type="text"
          placeholder="Search APIs..."
          className="search-input"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
        <div className="block-list api-list" onWheel={(e) => e.stopPropagation()}>
          {categoryOrder.map(categoryKey => {
            const apis = groupedApis[categoryKey];
            if (!apis || apis.length === 0) return null;

            const catInfo = categoryInfo[categoryKey];
            const isExpanded = expandedCategories[categoryKey];

            return (
              <div key={categoryKey} className="api-category">
                <div className="api-category-header" onClick={() => toggleCategory(categoryKey)}>
                  <span className="category-name">{catInfo.name}</span>
                  <span className="category-count">({apis.length})</span>
                  <span className="category-toggle">{isExpanded ? '▼' : '▶'}</span>
                </div>
                {isExpanded && (
                  <div className="api-category-content">
                    {apis.map(([key, schema]) => {
                      const logoUrl = getLogoInfo(key, schema.name);
                      const authIcon = getAuthIcon(schema.auth_type);
                      const rateLimit = schema.rate_limit;

                      return (
                        <div
                          key={key}
                          className="block-list-item"
                          onClick={() => addBlock('API', { schema_key: key, name: schema.name })}
                          onDragStart={(event) => onDragStart(event, { type: 'API', params: { schema_key: key, name: schema.name } })}
                          draggable
                          title={`${schema.name}${authIcon ? ' (Auth Required)' : ''}${rateLimit ? `\nRate Limit: ${rateLimit}` : ''}\n${schema.description || schema.doc_url}`}
                        >
                          <div className="api-avatar-container">
                            {logoUrl ? (
                              <>
                                <div className="api-logo-wrapper">
                                  <img
                                    src={logoUrl}
                                    alt={schema.name}
                                    className="api-logo"
                                    onError={(e) => {
                                      e.target.parentElement.style.display = 'none';
                                      e.target.parentElement.nextSibling.style.display = 'flex';
                                    }}
                                  />
                                </div>
                                <div
                                  className="api-avatar"
                                  style={{ backgroundColor: getApiColor(schema.name), display: 'none' }}
                                >
                                  {schema.name.charAt(0).toUpperCase()}
                                </div>
                              </>
                            ) : (
                              <div
                                className="api-avatar"
                                style={{ backgroundColor: getApiColor(schema.name) }}
                              >
                                {schema.name.charAt(0).toUpperCase()}
                              </div>
                            )}
                            {authIcon && <span className="auth-badge" title="Authentication required">{authIcon}</span>}
                          </div>
                          <div className="block-list-item-content">
                            <div className="block-list-item-name">
                              {schema.name}
                            </div>
                            <div className="block-list-item-desc">{schema.description || schema.doc_url}</div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
      <div className="controls-section logic-blocks-section">
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
    </aside>
  );
};

export default ControlPanel;
