import React, {useState, useEffect, useRef, useCallback} from 'react';
import Editor, {useMonaco} from '@monaco-editor/react';
import {useStore} from '../helpers/store';

const ReactIDE = () => {
    const nodes = useStore((state) => state.nodes);
    const updateNode = useStore((state) => state.updateNode);
    const editorTheme = useStore((state) => state.editorTheme);
    const updateOutputValue = useStore((state) => state.updateOutputValue);
    const executeGraph = useStore((state) => state.executeGraph);
    const edges = useStore((state) => state.edges);
    // Auto-seek the React node directly, ignoring selection.
    const reactNode = useStore(state =>
        (state.nodes || []).find(n => n.data?.type === 'REACT' || n.data?.block_type === 'REACT')
    );
    const reactNodeId = reactNode?.id;

    const [jsx, setJsx] = useState('');
    const [css, setCss] = useState('');
    const [activeTab, setActiveTab] = useState('jsx'); // 'jsx' or 'css'
    const [isCollapsed, setIsCollapsed] = useState(false); // New state for collapse
    const iframeRef = useRef(null);
    const [iframeReady, setIframeReady] = useState(false);
    const monaco = useMonaco();

    useEffect(() => {
        if (monaco && editorTheme) {
            monaco.editor.defineTheme('flow-theme', editorTheme);
            monaco.editor.setTheme('flow-theme');
        }
    }, [monaco, editorTheme]);

    // Helper to convert inputs/outputs to array format
    const toPortArray = (portsData, metaData) => {
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

    // Compute props for the React preview by resolving connections. If an input is connected,
    // use the source node's output value; otherwise fall back to the input.value stored on the node.
    const previewProps = React.useMemo(() => {
        if (!reactNode) return {};

        const props = {};
        const inputsArray = toPortArray(reactNode.data.inputs, reactNode.data.input_meta);

        inputsArray.forEach(input => {
            // Find an edge that connects into this input
            const incoming = edges.find(e => e.target === reactNode.id && e.targetHandle === input.key);
            if (incoming) {
                // find source node
                const src = nodes.find(n => n.id === incoming.source);
                if (src) {
                    const outputsArray = toPortArray(src.data.outputs, src.data.output_meta);
                    const out = outputsArray.find(o => o.key === incoming.sourceHandle);
                    props[input.key] = out?.value;
                } else {
                    props[input.key] = input.value;
                }
            } else {
                props[input.key] = input.value;
            }
        });

        return props;
    }, [nodes, edges, reactNode]);

    useEffect(() => {
        if (reactNode) {
            setJsx(reactNode.data.jsx_code || '');
            setCss(reactNode.data.css_code || '');
        } else {
            setJsx('');
            setCss('');
        }
    }, [reactNode]); // Only re-sync when the react node itself changes

    // Listen for sandbox ready messages so we don't post before iframe is initialized
    useEffect(() => {
        const onMessage = (event) => {
            if (!event?.data) return;
            if (event.data.type === 'SANDBOX_READY') {
                setIframeReady(true);
            }
        };
        window.addEventListener('message', onMessage);
        return () => window.removeEventListener('message', onMessage);
    }, []);

    // Handle local changes before syncing to store (debounce could be added here)
    const handleJsxChange = (value) => {
        setJsx(value);
        if (reactNodeId) {
            updateNode(reactNodeId, {jsx_code: value});
        }
    };

    const handleCssChange = (value) => {
        setCss(value);
        if (reactNodeId) {
            updateNode(reactNodeId, {css_code: value});
        }
    };

    // --- PARSING LOGIC ---
    // Parse the JSX code to find props and update the node's inputs/outputs
    const parseAndSyncPorts = useCallback((code) => { // This function is now stable
        // Get the latest state directly from the store to avoid stale closures
        // and to prevent this callback from being recreated on every render.
        const state = useStore.getState();
        const selectedNode = state.nodes.find(n => n.data?.type === 'REACT' || n.data?.block_type === 'REACT');

        // Guard clauses using the fresh data
        if (!selectedNode) {
            return;
        }

        // Regex to find the props destructuring pattern in:
        // 1. export default function Name({ prop1, prop2 }) ...
        // 2. const Name = ({ prop1, prop2 }) => ...
        const functionRegex = /export\s+default\s+function\s+\w*\s*\(\s*\{\s*([^}]+)\s*\}\s*\)/;
        const arrowRegex = /(?:const|let|var)\s+\w+\s*=\s*\(\s*\{\s*([^}]+)\s*\}\s*\)\s*=>/;

        const match = code.match(functionRegex) || code.match(arrowRegex);

        if (match && match[1]) {
            // First, remove all comments (line and block) from the captured group
            const propsString = match[1].replace(/\/\*[\s\S]*?\*\/|\/\/.*/g, '');
            
            // Extract prop names from the cleaned string
            const props = propsString
                .split(',')
                .map(p => p.trim().split('=')[0].split(':')[0].trim()) // Handle defaults (=) and renaming (:)
                .filter(p => p); // Filter out any empty strings that might result from trailing commas

            const newInputs = [];
            const newOutputs = [];

            props.forEach(prop => {
                if (prop === 'onWorkflowOutputChange') return; // Ignore system prop

                // Convention: Props starting with 'on' followed by uppercase are Outputs (Events)
                if (prop.startsWith('on') && prop.length > 2 && prop[2] === prop[2].toUpperCase()) {
                    newOutputs.push({key: prop, data_type: 'any'});
                } else {
                    newInputs.push({key: prop, data_type: 'any'});
                }
            });

            // Compare with current ports to avoid unnecessary updates
            const currentInputsData = selectedNode.data?.inputs;
            const currentOutputsData = selectedNode.data?.outputs;

            // Convert to array format for comparison
            const currentInputs = Array.isArray(currentInputsData)
                ? currentInputsData
                : (typeof currentInputsData === 'object' && currentInputsData !== null)
                    ? Object.keys(currentInputsData).map(key => ({ key }))
                    : [];
            const currentOutputs = Array.isArray(currentOutputsData)
                ? currentOutputsData
                : (typeof currentOutputsData === 'object' && currentOutputsData !== null)
                    ? Object.keys(currentOutputsData).map(key => ({ key }))
                    : [];

            const inputsChanged = JSON.stringify(newInputs.map(i => i.key).sort()) !== JSON.stringify(currentInputs.map(i => i.key).sort());
            const outputsChanged = JSON.stringify(newOutputs.map(o => o.key).sort()) !== JSON.stringify(currentOutputs.map(o => o.key).sort());

            if (inputsChanged || outputsChanged) {
                updateNode(selectedNode.id, {inputs: newInputs, outputs: newOutputs});
            }
        }
    }, [updateNode]);

    // Debounce the parsing so it doesn't run on every keystroke
    useEffect(() => {
        const timer = setTimeout(() => {
            parseAndSyncPorts(jsx);
        }, 1000); // 1 second debounce
        return () => clearTimeout(timer);
    }, [jsx, parseAndSyncPorts]);

    // --- PREVIEW / SANDBOX LOGIC ---
    // Send code and props to the sandbox iframe
    useEffect(() => {
        if (!reactNode || !iframeRef.current) return;
        // Wait until iframe signals it's ready
        if (!iframeReady) return;

        // use previewProps directly
        const message = {
            type: 'RENDER_COMPONENT',
            payload: {
                jsx: jsx,
                css: css,
                props: previewProps
            }
        };

        try {
            iframeRef.current.contentWindow.postMessage(message, '*');
        } catch (e) {
            // ignore postMessage errors from cross-origin or timing
            console.warn('Failed to postMessage to sandbox:', e);
        }
    }, [jsx, css, previewProps, iframeReady, reactNode]);

    // Listen for messages from sandbox (updates to outputs, execution triggers)
    useEffect(() => {
        const handleMessage = (event) => {
            if (!reactNodeId) return;

            const {type, payload} = event.data;
            if (type === 'SET_WORKFLOW_OUTPUT') {
                updateOutputValue(reactNodeId, payload.key, payload.value);
            } else if (type === 'TRIGGER_WORKFLOW_EXECUTION') {
                executeGraph();
            }
        };

        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, [reactNodeId, executeGraph, updateOutputValue]);


    if (!reactNode) {
        return (
            <div className="react-ide-panel react-ide-empty">
                <p>No React I/O node found in the workflow.</p>
                <p>Add a <strong>React I/O</strong> block from the Logic Blocks panel to activate the editor.</p>
            </div>
        );
    }

    return (
        <div 
            className={`react-ide-panel ${isCollapsed ? "collapsed" : ""}`}
            onClick={isCollapsed ? () => setIsCollapsed(false) : undefined}
            title={isCollapsed ? "Click to expand" : ""}
        >
            <div className="ide-header">
                <div className="ide-tabs">
                    <button
                        className={`ide-tab ${activeTab === 'jsx' ? 'active' : ''}`}
                        onClick={() => setActiveTab('jsx')}
                    >
                        JSX
                    </button>
                    <button
                        className={`ide-tab ${activeTab === 'css' ? 'active' : ''}`}
                        onClick={() => setActiveTab('css')}
                    >
                        CSS
                    </button>
                </div>
                <div className="ide-node-name">{reactNode?.data?.name || 'React I/O'}</div>
                <button
                    className="collapse-toggle"
                    onClick={(e) => {
                        e.stopPropagation(); // Prevent triggering panel onClick
                        setIsCollapsed(!isCollapsed);
                    }}
                    title={isCollapsed ? "Expand" : "Collapse"}
                >
                    {isCollapsed ? "⬅" : "➡"}
                </button>
            </div>

            <div className="ide-editor-container">
                {activeTab === 'jsx' && (
                    <Editor
                        height="100%"
                        defaultLanguage="javascript"
                        theme="flow-theme"
                        value={jsx}
                        onChange={handleJsxChange}
                        options={{
                            minimap: {enabled: false},
                            fontSize: 12,
                            padding: {top: 10}
                        }}
                    />
                )}
                {activeTab === 'css' && (
                    <Editor
                        height="100%"
                        defaultLanguage="css"
                        theme="flow-theme"
                        value={css}
                        onChange={handleCssChange}
                        options={{
                            minimap: {enabled: false},
                            fontSize: 12,
                            padding: {top: 10}
                        }}
                    />
                )}
            </div>

            <div className="ide-preview-container">
                <div className="preview-label">Live Preview</div>
                <div className="preview-wrapper">
                    <iframe
                        ref={iframeRef}
                        src="/sandbox.html"
                        title="React Component Preview"
                        sandbox="allow-scripts allow-same-origin"
                        className="preview-iframe"
                    />
                </div>
            </div>
        </div>
    );
};

export default ReactIDE;
