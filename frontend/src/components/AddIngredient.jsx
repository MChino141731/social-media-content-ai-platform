// src/components/AddIngredient.jsx
import { useState } from "react";

function AddIngredient() {
  const [green, setGreen] = useState("");
  const [red, setRed] = useState("");
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const handleAddGreen = async (e) => {
    e.preventDefault();
    setError(null);
    setMessage(null);

    if (!green.trim()) {
      setError("Please enter an ingredient to add to the green list");
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/add_green", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ingredient: green }),
      });

      if (!res.ok) {
        setError(`Backend error: ${res.status}`);
        return;
      }

      setMessage(`✅ Ingredient '${green}' added to the green list!`);
      setGreen("");
    } catch (err) {
      setError(`Connection error: ${err.message}`);
    }
  };

  const handleAddRed = async (e) => {
    e.preventDefault();
    setError(null);
    setMessage(null);

    if (!red.trim()) {
      setError("Please enter an ingredient to add to the red list");
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/add_red", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ingredient: red }),
      });

      if (!res.ok) {
        setError(`Backend error: ${res.status}`);
        return;
      }

      setMessage(`❌ Ingredient '${red}' added to the red list!`);
      setRed("");
    } catch (err) {
      setError(`Connection error: ${err.message}`);
    }
  };

  return (
    <div className="mt-10 w-full max-w-3xl mx-auto">
      {/* Green form */}
      <form
        onSubmit={handleAddGreen}
        className="mb-6 flex flex-col gap-3 bg-green-50 p-4 rounded-lg shadow"
      >
        <label className="font-semibold">
          Ingredient to add to the green list:
        </label>
        <input
          type="text"
          placeholder="e.g. Aloe Vera"
          value={green}
          onChange={(e) => setGreen(e.target.value)}
          className="p-3 border rounded w-full"
        />
        <button className="bg-green-300 text-black px-6 py-3 rounded font-semibold hover:bg-green-400 w-auto mx-auto">
          🟢 Add Green
        </button>
      </form>

      {/* Red form */}
      <form
        onSubmit={handleAddRed}
        className="mb-6 flex flex-col gap-3 bg-red-50 p-4 rounded-lg shadow"
      >
        <label className="font-semibold">
          Ingredient to add to the red list:
        </label>
        <input
          type="text"
          placeholder="e.g. Parabens"
          value={red}
          onChange={(e) => setRed(e.target.value)}
          className="p-3 border rounded w-full"
        />
        <button className="bg-red-300 text-black px-6 py-3 rounded font-semibold hover:bg-red-400 w-auto mx-auto">
          ❌ Add Red
        </button>
      </form>

      {message && <p className="text-green-600 font-bold">{message}</p>}
      {error && <p className="text-red-600 font-bold">{error}</p>}
    </div>
  );
}

export default AddIngredient;
