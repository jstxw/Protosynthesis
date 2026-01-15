import { useStore } from '../helpers/store';
import './ChatButton.css';

const ChatButton = () => {
  const toggleChatPanel = useStore((state) => state.toggleChatPanel);
  const chatPanelOpen = useStore((state) => state.chatPanelOpen);

  // Don't show button if chat is already open
  if (chatPanelOpen) {
    return null;
  }

  return (
    <button
      className="floating-chat-button"
      onClick={toggleChatPanel}
      title="Open AI Assistant"
    >
      <svg
        width="32"
        height="32"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Message square icon */}
        <path
          d="M21 15C21 15.5304 20.7893 16.0391 20.4142 16.4142C20.0391 16.7893 19.5304 17 19 17H7L3 21V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H19C19.5304 3 20.0391 3.21071 20.4142 3.58579C20.7893 3.96086 21 4.46957 21 5V15Z"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {/* Three horizontal lines (chat text) */}
        <line x1="8" y1="8" x2="16" y2="8" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
        <line x1="8" y1="12" x2="14" y2="12" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
      </svg>
    </button>
  );
};

export default ChatButton;
