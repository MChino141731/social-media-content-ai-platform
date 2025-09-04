import { useState } from "react";
import Navbar from "../components/Navbar";

function CreateProduct() {
  const [hint, setHint] = useState("");
  const [message, setMessage] = useState(null);
  const [productDetails, setProductDetails] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setMessage(null);
    setProductDetails(null);

    if (!hint.trim()) {
      setError("Please enter a product idea");
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/create_product", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ hint }),
      });

      if (!res.ok) {
        setError(`Backend error: ${res.status}`);
        return;
      }

      const data = await res.json();
      setMessage(`✅ Product created: ${data.nome_prodotto || "(no name)"}`);
      setProductDetails({
        name: data.nome_prodotto,
        description: data.descrizione,
        ingredients: data.ingredienti || [],
        notes: data.note_sostenibilita,
        imageUrl: data.image_url,
      });
    } catch (err) {
      setError(`Connection error: ${err.message}`);
    }
  };

  return (
    <>
      <Navbar />
      <div className="p-5 flex flex-col items-center min-h-screen bg-gray-900">
        <h1 className="text-3xl md:text-4xl font-bold mb-8 text-white text-center">
          New Product
        </h1>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full max-w-3xl">
          <input
            type="text"
            placeholder="Es.: Crea un nuovo shampoo..."
            value={hint}
            onChange={(e) => setHint(e.target.value)}
            className="p-3 border rounded w-full bg-white text-black"
          />
          <button className="bg-green-500 text-white px-6 py-3 rounded font-semibold hover:bg-green-600 w-auto mx-auto">
            Generate Product
          </button>
        </form>

        {error && <p className="text-red-500 mt-4">{error}</p>}
        {message && <p className="text-green-600 mt-4 font-bold">{message}</p>}

        {productDetails && (
          <div className="mt-6 w-full max-w-3xl text-left bg-white p-4 rounded shadow">
            <h2 className="font-bold text-xl mb-2">Generated Product:</h2>
            <p><strong>Name:</strong> {productDetails.name}</p>
            <p><strong>Description:</strong> {productDetails.description}</p>
            <p><strong>Ingredients:</strong> {productDetails.ingredients.join(", ")}</p>
            <p><strong>Sustainability notes:</strong> {productDetails.notes}</p>
            {productDetails.imageUrl && (
              <img
                src={productDetails.imageUrl}
                alt="Generated Product"
                className="max-w-sm mt-3 mx-auto rounded"
              />
            )}
          </div>
        )}
      </div>
    </>
  );
}

export default CreateProduct;
