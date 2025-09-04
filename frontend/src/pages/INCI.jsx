// src/pages/INCI.jsx
import { useState } from "react";
import Navbar from "../components/Navbar";
import AddIngredient from "../components/AddIngredient";

function INCI() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setResults([]);

    const ingredientsList = query
      .split(",")
      .map((i) => i.trim())
      .filter((i) => i);

    if (ingredientsList.length === 0) {
      setError("Please enter at least one ingredient");
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/check_inci", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: ingredientsList.join(", ") }),
      });

      if (!res.ok) {
        setError(`Backend error INCI: ${res.status}`);
        return;
      }

      const data = await res.json();
      setResults(data.results || []);
    } catch (err) {
      setError(`Connection error: ${err.message}`);
    }
  };

  return (
    <>
      <Navbar />
      <div className="p-5 flex flex-col items-center min-h-screen bg-gray-900">
        <h1 className="text-3xl md:text-4xl font-bold mb-8 text-white text-center">
          Check INCI
        </h1>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full max-w-3xl">
          <textarea
            placeholder="Enter ingredients list separated by commas"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="p-3 border rounded w-full bg-white text-black"
            rows={4}
          />
          <button className="bg-blue-500 text-white px-6 py-3 rounded font-semibold hover:bg-blue-600 w-auto mx-auto">
            Check INCI
          </button>
        </form>

        {error && <p className="text-red-500 mt-4">{error}</p>}

        {results.length > 0 && (
          <div className="mt-6 w-full max-w-3xl overflow-x-auto bg-white p-4 rounded shadow">
            <table className="border-collapse border border-gray-300 w-full text-left">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border px-3 py-2">Ingredient</th>
                  <th className="border px-3 py-2">Status</th>
                </tr>
              </thead>
              <tbody>
                {results.map((item, index) => (
                  <tr key={index}>
                    <td className="border px-3 py-2">{item.ingrediente}</td>
                    <td className="border px-3 py-2">
                      {item.status === "harmful" ? (
                        <span className="text-red-600">●</span>
                      ) : item.status === "sustainable" ? (
                        <span className="text-green-600">●</span>
                      ) : (
                        <span className="text-gray-500">●</span>
                      )}
                      {item.source === "llm" && (
                        <span className="ml-2 text-sm text-gray-500">(via LLM)</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* AddIngredient stays at the bottom */}
        <div className="mt-10 w-full max-w-3xl">
          <AddIngredient />
        </div>
      </div>
    </>
  );
}

export default INCI;
