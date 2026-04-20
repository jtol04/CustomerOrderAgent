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
      const response = await fetch('http://localhost:8000/query', {
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
      <section id="center">
        <div>
          <h1>Welcome!</h1>
          <p>
            I am a customer order agent. I can show you orders that exist
            in the system,<br></br> or predict the total price of an order given
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
