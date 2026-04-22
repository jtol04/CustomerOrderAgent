import type { message } from "../interfaces/interfaces"

export const PreviewMessage = ( { message } : { message : message; }) => {

    return (
        <div className={`max-w-full p-2 rounded-lg mx-10 ${message.role === 'user' ? 'bg-blue-100 ml-auto' : 'bg-gray-100 mr-auto'}`}>
            <pre className="whitespace-pre-wrap text-sm font-sans">{message.content}</pre>
        </div>
    );
};

export const ThinkingMessage = () => {
    return (
        <div className="max-w-md p-2 rounded-lg bg-gray-100 mr-auto mx-10">
            <pre className="whitespace-pre-wrap text-sm font-sans">Thinking...</pre>
        </div>
    );
};