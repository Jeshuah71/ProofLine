import { useState } from "react";
import "./App.css";

// Read the API URL form our environment
const API_URL = import.meta.env.VITE_API_URL;

function App() {
  // Store the job message entered by the user 
  const [message, setMessage] = useState("");

  // Store feedback after clicking Analyze 
  const [status, setStatus] = useState("");

  // Store the warning returned by python 
  const [warnings, setWarnings] = useState<string[]>([]);

  // Store recommendations returned by our backend
  const  [recommendations, setRecommendations] = useState<string[]>([]);

  async function handleAnalyze() {
    
    // Clear recommendations from the previous analysis
    setRecommendations([]);

    // Clear the previous analysis results
    setWarnings([]);

    // Remove unnecessary spaces
    const cleanMessage = message.trim();
    // Check whether the message is empty
    if (cleanMessage === "") {
      setStatus("Please enter a job offer first.");
      return;
    }

    // Require at least 20 characters
    if (cleanMessage.length < 20) {
      setStatus("Please enter at least 20 characters.");
      return;
    }

    setStatus("Analyzing message...");

    try {
      // Send the message to our Python backend
      const response = await fetch(
        `${API_URL}/analyze`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            message: cleanMessage,
          }),
        }
      );

      // Check wether the request succeeded
      if(!response.ok) {
        throw new Error("API request failed");
      }

      // Convert the JSON response into a JavaScript object
      const data = await response.json();

      // Save the recommendations returned by Python 
      setRecommendations(data.recommendations);

      // Save the warning from our backend 
      setWarnings(data.warnings);

      // Update the status message
      setStatus(`Analysis completed: ${data.assessment}`);
    } catch {
      setStatus("Could not connect to the backend.");
    }
  }
  return (
    <main className="app-container">
      {/* Application header */}
      <header className="app-header">
        <h1>Proofline</h1>
        <span>Job Offer Safety Checker</span>
      </header>

      {/* Introduction */}
      <section className="hero">
        <h2>Before you accept, check the signs.</h2>
        <p>
          Analyze job offers and recruiting messages
          for potential warning signs.
        </p>
      </section>

      {/* Job offer input */}
      <section className="analysis-card">
        <h3>Analyze a Job Offer</h3>

        <textarea
          placeholder="Paste a job offer or recruiting message..."
          rows={8}
          value={message}
          onChange={(event) => setMessage(event.target.value)}
        />

        <p className="character-count">
          {message.length} characters
        </p>

        <button type="button" onClick={handleAnalyze}>
          Analyze Message
        </button>

        {/* Analysis status */}
        {status && <p className="status">{status}</p>}

        {/* Detection results */}
        {status.startsWith("Analysis completed") && (
          <div 
            className={`warnings ${
              warnings.length === 0
                ? "no-warnings"
                : warnings.length === 1
                  ? "one-warning"
                  : "many-warnings"
            }`}
          >
            <h3>Analysis Results</h3>

            {warnings.length > 0 ?(
              <ul>
                {warnings.map((warning, index) => (
                  <li key={index}> {warning}</li>
                ))}
              </ul>
            ) : (
              <p>No watching warning signs were detected.</p>
            )}
          </div>
        )}

      </section>

      {/* Show recommendations when available */}
        <section className="recommendations">
          <h3>Recommended Actions</h3>

          <ul>
            {recommendations.map((recommendation, index) => (
              <li key={index}>
                {recommendation}
              </li>
            ))}
          </ul>
        </section>
      
      <footer>
        Proofline help identify warning signs 
        It does not verify job offers.
      </footer>
    </main>
  );
}

export default App;