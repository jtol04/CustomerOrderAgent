import { useState } from 'react'
import { ChatInput } from './components/chatbox'
import { Welcome } from './components/welcome'
import {  PreviewMessage, ThinkingMessage } from './components/message'
import type { message } from "./interfaces/interfaces"
import './App.css'

function App() {
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<message[]>([]);

  const handleSubmit = async (text?: string) => {
    const finalText = text ?? question;
    if (!finalText.trim()) return;

    setMessages(prev => [...prev, { role: 'user', content: finalText }]);
    setIsLoading(true);
    setQuestion('');

    try {
      const response = await fetch('http://localhost:8000/request/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request: finalText }),
      });
      const data = await response.json();
      setMessages(prev => [...prev, { role: 'agent', content: JSON.stringify(data, null, 2) }]);
      setQuestion('');
    } catch (err) {
      setMessages(prev => [...prev, { role: 'agent', content: 'Request failed' }]);
    } finally {
      setIsLoading(false)
    }
  };


  return (
    <section className="flex flex-col min-h-screen">
      <div className="flex flex-col justify-center flex-grow">
        {messages.length == 0 && <Welcome />}
        {messages.map((message, index) => (
          <PreviewMessage key={index} message={message} />
        ))}
        {isLoading && <ThinkingMessage/>}
      </div>

      <div className="sticky bottom-5">
        <ChatInput
          question={question}
          setQuestion={setQuestion}
          onSubmit={handleSubmit}
          isLoading={isLoading}
        />
      </div>
    </section>
        
  
  );
}

export default App
