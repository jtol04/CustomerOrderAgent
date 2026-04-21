interface ChatInputProps {
    question: string;
    setQuestion: (question: string) => void;
    onSubmit: (text?: string) => void;
    isLoading: boolean;

}

export function ChatInput({ question, setQuestion, onSubmit, isLoading }: ChatInputProps) {
    return (
        <div className="relative w-100 mx-auto mt-5">
            <textarea 
                className=" p-2 border rounded-lg w-100 h-20 text-[15px] placeholder:text-gray-500 resize-none"
                value={question}
                
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                    if (e.key === 'Enter' && !isLoading) {
                        e.preventDefault;
                        onSubmit(question);
                    }
                }}
                disabled={isLoading}
                placeholder="Ask me a question about customer orders..."
            />
            <button
                className="px-2 rounded-full border text-[15px] absolute bottom-3.5 right-2 bg-white hover:bg-gray-800 hover:text-white"
                onClick={() => onSubmit(question)}
                disabled={isLoading || !question.trim()}
            >
                {isLoading ? 'Send' : 'Send'}
            </button>
        </div>
    );
}