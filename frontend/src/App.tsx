import { useState } from 'react'
import { ChatInput } from './components/chatbox'
import './App.css'

function App() {
  const [question, setQuestion] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  const handleSubmit = async (text?: string) => {
    const finalText = text ?? question;
    if (!finalText.trim()) return;

    setIsLoading(true);
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/request/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ request: finalText }),
      });
      const data = await response.json();
      setResult(data);
      setQuestion('');
    } catch (err) {
      setResult({ error: 'Request failed' });
    } finally {
      setIsLoading(false)
    }
  };


  return (
    <>
      <section className="flex items-center justify-center">
        <div className="p-4">
          
          <h1 className="text-center text-5xl font-bold">Welcome!</h1>
          <p className="text-center text-lg mx-60">
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

            {result && (<pre>{JSON.stringify(result, null, 2)}</pre>)}
        </div>
      </section>
    </>
  );
}

export default App
