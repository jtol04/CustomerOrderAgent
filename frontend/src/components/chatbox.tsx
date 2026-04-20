interface ChatInputProps {
    question: string;
    setQuestion: (question: string) => void;
    onSubmit: (text?: string) => void;
    isLoading: boolean;

}

export function ChatInput({ question, setQuestion, onSubmit, isLoading }: ChatInputProps) {
    return (
        <div>
            <input 
                style={{ width: '500px', height: '20px' }}
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' && !isLoading) {
                        onSubmit(question);
                    }
                }}
                disabled={isLoading}
                placeholder="Ask me a question about customer orders..."
            />
            <button
                onClick={() => onSubmit(question)}
                disabled={isLoading || !question.trim()}
            >
                {isLoading ? 'Sending...' : 'Send'}
            </button>
        </div>
    );
}