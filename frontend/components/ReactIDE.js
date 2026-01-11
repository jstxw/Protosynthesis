import React, {useState, useEffect, useRef} from 'react';
import Editor from '@monaco-editor/react';
import {useStore} from '../helpers/store';

const ReactIDE = () => {
    const nodes = useStore((state) => state.nodes);
    const selectedNodeId = useStore((state) => state.selectedNodeId);
    const updateNode = useStore((state) => state.updateNode);
    const updateOutputValue = useStore((state) => state.updateOutputValue);
    const executeGraph = useStore((state) => state.executeGraph);
    const edges = useStore((state) => state.edges);

    const [jsx, setJsx] = useState('');
    const [css, setCss] = useState('');
    const [activeTab, setActiveTab] = useState('jsx'); // 'jsx' or 'css'
    const iframeRef = useRef(null);
    const [iframeReady, setIframeReady] = useState(false);

    const selectedNode = nodes.find(n => n.id === selectedNodeId);
    const isReactNode = selectedNode?.type === 'REACT';

    // Compute props for the React preview by resolving connections. If an input is connected,
    // use the source node's output value; otherwise fall back to the input.value stored on the node.
    const previewProps = React.useMemo(() => {
        if (!isReactNode || !selectedNode) return {};

        const props = {};

        (selectedNode.data.inputs || []).forEach(input => {
            // Find an edge that connects into this input
            const incoming = edges.find(e => e.target === selectedNode.id && e.targetHandle === input.key);
            if (incoming) {
                // find source node
                const src = nodes.find(n => n.id === incoming.source);
                if (src) {
                    const out = (src.data.outputs || []).find(o => o.key === incoming.sourceHandle);
                    props[input.key] = out?.value;
                } else {
                    props[input.key] = input.value;
                }
            } else {
                props[input.key] = input.value;
            }
        });

        return props;
    }, [nodes, edges, selectedNodeId, isReactNode, selectedNode]);

    useEffect(() => {
        if (isReactNode) {
            setJsx(selectedNode.data.jsx_code || '');
            setCss(selectedNode.data.css_code || '');
        } else {
            setJsx('');
            setCss('');
        }
    }, [selectedNodeId, isReactNode, selectedNode?.data.jsx_code, selectedNode?.data.css_code]);

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
        if (selectedNodeId) {
            updateNode(selectedNodeId, {jsx_code: value});
        }
    };

    const handleCssChange = (value) => {
        setCss(value);
        if (selectedNodeId) {
            updateNode(selectedNodeId, {css_code: value});
        }
    };

    // --- PREVIEW / SANDBOX LOGIC ---
    // Send code and props to the sandbox iframe
    useEffect(() => {
        if (!isReactNode || !iframeRef.current) return;
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
    }, [jsx, css, previewProps, iframeReady, isReactNode, selectedNode]);

    // Listen for messages from sandbox (updates to outputs, execution triggers)
    useEffect(() => {
        const handleMessage = (event) => {
            if (!selectedNodeId) return;

            const {type, payload} = event.data;
            if (type === 'SET_WORKFLOW_OUTPUT') {
                updateOutputValue(selectedNodeId, payload.key, payload.value);
            } else if (type === 'TRIGGER_WORKFLOW_EXECUTION') {
                executeGraph();
            }
        };

        window.addEventListener('message', handleMessage);
        return () => window.removeEventListener('message', handleMessage);
    }, [selectedNodeId, executeGraph, updateOutputValue]);


    if (!isReactNode) {
        return (
            <div className="react-ide-empty">
                <p>Select a React Node to edit its code.</p>
            </div>
        );
    }

    return (
        <div className="react-ide-panel">
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
                <div className="ide-node-name">{selectedNode?.data?.name || 'React Node'}</div>
            </div>

            <div className="ide-editor-container">
                {activeTab === 'jsx' && (
                    <Editor
                        height="100%"
                        defaultLanguage="javascript"
                        theme="vs-dark"
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
                        theme="vs-dark"
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
