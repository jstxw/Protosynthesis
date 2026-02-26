'use client';

import { useState, useRef, useEffect } from 'react';
import { useStore } from '@/helpers/store';

export default function DialogueModal() {
    const dialoguePrompt = useStore((state) => state.dialoguePrompt);
    const submitDialogueResponse = useStore((state) => state.submitDialogueResponse);
    const [inputValue, setInputValue] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const inputRef = useRef(null);

    // Auto-focus and reset input when prompt appears
    useEffect(() => {
        if (dialoguePrompt) {
            setInputValue('');
            setIsSubmitting(false);
            // Small delay to ensure DOM is ready
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }, [dialoguePrompt]);

    if (!dialoguePrompt) return null;

    const handleSubmit = async () => {
        if (isSubmitting) return;
        setIsSubmitting(true);
        await submitDialogueResponse(dialoguePrompt.blockId, inputValue);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    // Format message content
    const messageContent = dialoguePrompt.message || 'Enter your response:';

    return (
        <div className="dialogue-modal-overlay">
            <div className="dialogue-modal">
                <div className="dialogue-modal-header">
                    <img src="/chat.svg" alt="" className="dialogue-modal-icon" />
                    <span>Dialogue Input</span>
                </div>

                <div className="dialogue-modal-message">
                    {messageContent}
                </div>

                <div className="dialogue-modal-input-area">
                    <input
                        ref={inputRef}
                        type="text"
                        className="dialogue-modal-input"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type your response..."
                        disabled={isSubmitting}
                        autoFocus
                    />
                </div>

                <div className="dialogue-modal-actions">
                    <button
                        className="dialogue-modal-submit"
                        onClick={handleSubmit}
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? 'Submitting...' : 'Submit'}
                    </button>
                </div>
            </div>
        </div>
    );
}
