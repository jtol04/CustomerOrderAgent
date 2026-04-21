import { useState } from 'react'
import { ChatInput } from './components/chatbox'
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
    <>
      <section className="flex items-center justify-center content-center min-h-screen">
        <div className="p-4">
          <h1 className="text-center text-5xl font-bold">Welcome!</h1>
          <p className="text-center text-lg mx-70">
            I am a customer order agent. I can show you orders that exist
            in the system, or predict the total price of an order given
            an item count per category (or multiple categories).
          </p>
          
          <ChatInput
            question={question}
            setQuestion={setQuestion}
            onSubmit={handleSubmit}
            isLoading={isLoading}
            />
        </div>
      </section>
    </>
  );
}

export default App
