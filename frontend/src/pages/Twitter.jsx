import { useState } from "react";
import Navbar from "../components/Navbar";

function Twitter() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [imageUrl, setImageUrl] = useState(null);
  const [error, setError] = useState(null);

  // Stati demo
  const [published, setPublished] = useState(false);
  const [tweetId, setTweetId] = useState(null);
  const [topTweets, setTopTweets] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setAnswer("");
    setImageUrl(null);
    setPublished(false);
    setTweetId(null);
    setTopTweets(null);

    if (!question.trim()) {
      setError("Please enter a prompt");
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: question, platform: "twitter" }),
      });

      if (!res.ok) {
        setError(`Backend error: ${res.status}`);
        return;
      }

      const data = await res.json();
      setAnswer(data.answer || "No response");
      setImageUrl(data.image_url || null);
    } catch (err) {
      setError(`Connection error: ${err.message}`);
    }
  };

  return (
    <>
      <Navbar />
      <div className="p-5 flex flex-col items-center min-h-screen bg-gray-900">
        <h1 className="text-3xl md:text-4xl font-bold mb-8 text-white text-center">
          Twitter
        </h1>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4 w-full max-w-3xl">
          <textarea
            rows="4"
            placeholder="Enter your prompt..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            className="p-3 border rounded w-full bg-white text-black"
          />
          <button className="bg-blue-500 text-white px-6 py-3 rounded font-semibold hover:bg-blue-600 w-auto mx-auto">
            Generate
          </button>
        </form>

        {error && <p className="text-red-500 mt-4">{error}</p>}

        {answer && (
          <div className="mt-6 w-full max-w-3xl text-left">
            <h2 className="font-bold text-xl mb-2 text-white">Generated Tweet:</h2>
            <p className="p-3 border rounded bg-white text-black">{answer}</p>

            {/* Demo pubblicazione */}
            {!published ? (
              <div className="mt-4 flex items-center gap-2">
                <button
                  onClick={() => {
                    console.log("Publishing tweet:", answer);
                    setPublished(true);
                    setTweetId("1234567890"); // mock id
                  }}
                  className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
                >
                  Publish on Twitter
                </button>
                <span className="bg-yellow-400 text-black px-2 py-1 rounded font-semibold text-sm">
                  Demo
                </span>
              </div>
            ) : (
              <div className="mt-4 space-y-3">
                <p className="text-green-600 font-semibold">
                  ✅ Tweet published! (ID: {tweetId})
                </p>

                {/* Pulsante demo top tweet */}
                <button
                  onClick={() => {
                    setTopTweets([
                      { id: "111", text: "Top tweet #1", likes: 25, retweets: 7, comments: 3 },
                      { id: "222", text: "Top tweet #2", likes: 18, retweets: 4, comments: 1 },
                      { id: "333", text: "Top tweet #3", likes: 12, retweets: 2, comments: 0 },
                    ]);
                  }}
                  className="bg-yellow-500 text-black px-4 py-2 rounded hover:bg-yellow-600"
                >
                  Show top tweets (Demo)
                </button>

                {topTweets && (
                  <div className="mt-3 space-y-3 p-3 bg-gray-100 rounded-lg text-black">
                    {topTweets.map((t) => (
                      <div key={t.id} className="border-b pb-2">
                        <p className="font-semibold">{t.text}</p>
                        <p>👍 {t.likes}  🔁 {t.retweets}  💬 {t.comments}</p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {imageUrl && (
          <div className="mt-6 w-full max-w-3xl">
            <h2 className="font-bold text-xl mb-2 text-white">Generated Image:</h2>
            <img src={imageUrl} alt="Generated" className="rounded shadow max-w-full" />
          </div>
        )}
      </div>
    </>
  );
}

export default Twitter;
