import { useStore } from '../helpers/store';

const ReactIDEButton = () => {
    const openReactIDE = useStore((state) => state.openReactIDE);
    const reactIDEOpen = useStore((state) => state.reactIDEOpen);
    const hasReactNode = useStore((state) =>
        (state.nodes || []).some(n => n.data?.type === 'REACT' || n.data?.block_type === 'REACT')
    );

    // Only show when a React block exists and IDE is not already open
    if (!hasReactNode || reactIDEOpen) {
        return null;
    }

    return (
        <button
            className="floating-react-ide-button"
            onClick={openReactIDE}
            title="Open React IDE"
        >
            <svg
                width="28"
                height="28"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
            >
                {/* Code/brackets icon */}
                <polyline points="16 18 22 12 16 6" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                <polyline points="8 6 2 12 8 18" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
        </button>
    );
};

export default ReactIDEButton;
