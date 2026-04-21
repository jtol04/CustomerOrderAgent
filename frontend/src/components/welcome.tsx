export const Welcome = () => {
    return (
        <div>
        <h1 className="text-center text-5xl font-bold">Welcome!</h1>
          <p className="text-center text-lg mx-70 p-4">
            I am a customer order agent. I can show you orders that exist
            in the system, or predict the total price of an order given
            an item count per category (or multiple categories).
          </p>
        </div>
    );
};