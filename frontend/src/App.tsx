import { useState } from "react";
import "./App.css";

// Read the API URL form our environment
const API_URL = import.meta.env.VITE_API_URL;

type RegistrationResult = {
  status: "checked" | "unavailable" | "no-reference";
  domain?: string;
  registered_at?: string | null;
};

type URLAnalysisResult = {
  status: "checked" | "invalid";
  hostname?: string;
  signals: string[];
};

type PostingAnalysisResult = {
  prediction: number;
  model_score: number;
  threshold: number;
  scope: string;
  rule_signals: string[];
  review_recommended: boolean;
};

type ActiveSection = "offer" | "posting" | "tools";


function App() {

  // Store domain validation messages 
  const [domainError, setDomainError] = useState<string | null>(null);
  // Store the job message entered by the user 
  const [message, setMessage] = useState("");

  // Store feedback after clicking Analyze 
  const [status, setStatus] = useState("");

  // Store the warning returned by python 
  const [warnings, setWarnings] = useState<string[]>([]);

  // Store recommendations returned by our backend
  const  [recommendations, setRecommendations] = useState<string[]>([]);

  // Store the company name entered by the user
  const [companyName, setCompanyName] = useState("");

  // Store domain registration information 
  const [registration, setRegistration] = useState<RegistrationResult | null>(null);

  // Track whether the request is running 
  const [checkingDomain, setCheckingDomain] = useState(false);


  // Job posting information
  const [postingTitle, setPostingTitle] = useState("");
  const [postingDescription, setPostingDescription] = useState("");

  // ML and rule-based results
  const [postingResult, setPostingResult] =
  useState<PostingAnalysisResult | null>(null);

  // Loading and error states
  const [checkingPosting, setCheckingPosting] = useState(false);
  const [postingError, setPostingError] = useState("");
  
  type DomainCheck = {
    email_domain: string;
    website_domain: string;
    exact_match: boolean;
    is_subdomain: boolean;
    potential_lookalike: boolean;
  };

  type ReferenceCheck = {
    email_domain: string;
    reference_domain: string;
    matches_reference: boolean;
  };

  type ReferenceRecord = {
    domain: string;
    source: string;
    verified: boolean;
    checked_at?: string;
    verification_scope?: string;
  };

  // Store recruiter information entered by the user 
  const [recruiterEmail, setRecruiterEmail] = useState("");
  const [companyWebsite, setCompanyWebsite] = useState("");

  // Store domain comparison results
  const [domainCheck, setDomainCheck] = useState<DomainCheck | null>(null);

  // Store the company registery comparison
  const [referenceCheck, setReferenceCheck] = useState<ReferenceCheck | null>(null);

  // Store company refrence metadata
  const [referenceRecord, setReferenceRecord] = useState<ReferenceRecord | null>(null);

  // Store the URL entered by the user
  const [jobUrl, setJobUrl] = useState("");

  // Store the URL analysis results
  const [urlResult, setUrlResult] = useState<URLAnalysisResult | null>(null);

  // Track loading and errors
  const [checkingUrl, setCheckingURL] = useState(false);
  const [urlError, setUrlError] = useState("");

  const [activeSection, setActiveSection] = useState<ActiveSection>("offer");
  async function handleAnalyze() {

    setUrlResult(null);
    // Clear the previous company reference
    setReferenceRecord(null);

    // Clear the previous comparison
    setReferenceCheck(null);
    
    // 
    setDomainError(null);

    
    // Clear the previous domain comparison
    setDomainCheck(null);
    
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
            company_name: companyName.trim() || null, 
            recruiter_email: recruiterEmail.trim() || null,
            company_website: companyWebsite.trim() || null,

            // Include the job URL in the main analysis
            job_url: jobUrl.trim() || null,
          }),
        }
      );

      // Check wether the request succeeded
      if(!response.ok) {
        throw new Error("API request failed");
      }

      // Convert the JSON response into a JavaScript object
      const data = await response.json();

      // SAve the URL analysis returned by analyze
      setUrlResult(data.url_check ?? null);

      // Save source information from FastAPI
      setReferenceRecord(data.reference_check ?? null);

      // Save the comparison returned by FastAPI
      setReferenceCheck(data.reference_check ?? null);

      // Read the domain validation result 
      setDomainError(data.domain_error ?? null);

      // Save the comparison returned by FastAPI
      setDomainCheck(data.domain_check ?? null);

      // Save the recommendations returned by Python 
      setRecommendations(data.recommendations);

      // Save the warning from our backend 
      setWarnings(data.warnings);

      // Update the status message
      setStatus(
        data.warning_count === 0
          ? "Message analysis: No text warning patterns matched."
          : `Message analysis: ${data.assessment}`
      );
    } catch {
      setStatus("Could not connect to the backend.");
    }
  }

  async function handleCheckDomain() {
    // Clear the previous result 
    setRegistration(null);
    setCheckingDomain(true);

    try {
      // Send the company name as a query parameter
      const response = await fetch(
        `${API_URL}/domain-registration?company_name=${
          encodeURIComponent(companyName.trim())
        }`
      );

      if (!response.ok) {
        throw new Error("Domain lookup failed");
      }

      // Read the backend response
      const data: RegistrationResult = await response.json();
      setRegistration(data);
    } catch {
      setRegistration({ status: "unavailable" });
    } finally {
      // Stop showing the loading state
      setCheckingDomain(false);
    }
  }

  async function handleAnalyzeUrl() {
    // Prepare the URL
    const cleanUrl = jobUrl.trim();

    if (!cleanUrl) {
      setUrlError("Please enter a URL.");
      return;
    }

    // Reset previous results
    setUrlResult(null)
    setUrlError("");
    setCheckingURL(true);

    try {
      // Send the URL to FastAPI
      const response = await fetch(`${API_URL}/analyze-url`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url: cleanUrl }),
      });

      if (!response.ok) {
        throw new Error("URL analysis failed");
      }

      // Read and store the JSON response
      const data: URLAnalysisResult = await response.json();
      setUrlResult(data);
    } catch {
      setUrlError("Could not analyze the URL.");
    } finally {
      // Stop loading even if the request fails
      setCheckingURL(false);
    }
  }


  async function handleAnalyzePosting() {
    // Require a job description
    if (!postingDescription.trim()) {
      setPostingError("Please enter a job description.");
      return;
    }

    // Reset previous results
    setPostingResult(null);
    setPostingError("");
    setCheckingPosting(true);

    try {
      // Send the job posting to FastAPI
      const response = await fetch(`${API_URL}/analyze-posting`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: postingTitle.trim(),
          description: postingDescription.trim(),
        }),
      });

      if (!response.ok) {
        throw new Error("Posting analysis failed");
      }

      // Store the model and rule-based results
      const data: PostingAnalysisResult = await response.json();
      setPostingResult(data);

    } catch {
      setPostingError("Unable to analyze this posting.");
    } finally {
      setCheckingPosting(false);
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

      
      <nav className="analysis-navigation" aria-label="Analysis tools">
        <button
          type="button"
          className={activeSection === "offer" ? "active" : ""}
          aria-pressed={activeSection === "offer"}
          onClick={() => setActiveSection("offer")}
        >
          Job Offer
        </button>

        <button
          type="button"
          className={activeSection === "posting" ? "active" : ""}
          aria-pressed={activeSection === "posting"}
          onClick={() => setActiveSection("posting")}
        >
          Job Posting
        </button>

        <button
          type="button"
          className={activeSection === "tools" ? "active" : ""}
          aria-pressed={activeSection === "tools"}
          onClick={() => setActiveSection("tools")}
        >
          Domain Tools
        </button>
      </nav>


      {activeSection === "offer" && (
        <>
          {/* Job offer input */}
          <section className="analysis-card">
            <h3>Analyze a Job Offer</h3>

            <textarea
              placeholder="Paste a job offer or recruiting message..."
              rows={8}
              value={message}
              onChange={(event) => setMessage(event.target.value)}
            />
            <div className="company-fields">
              <label htmlFor="company-name">
                Company Name (optional)
              </label>

              <input
                id="company-name"
                type="text"
                placeholder="Enter company name"
                value={companyName}
                onChange={(event) => setCompanyName(event.target.value)}
              />
        
            {/* Oprional recruiter information */}
        
              <label htmlFor="recruiter-email">
                Recruiter Email (optional)
              </label>
              <input
                id="recruiter-email"
                type="email"
                placeholder="recruiter@example.com"
                value={recruiterEmail}
                onChange={(event) => setRecruiterEmail(event.target.value)}
              />
          
              <label htmlFor="company-website">
                Company Website (optional)
              </label>

              <input
                id="company-website"
                type="url"
                placeholder="https://example.com"
                value={companyWebsite}
                onChange={(event) => setCompanyWebsite(event.target.value)}
              />
            </div>

            <p className="character-count">
              {message.length} characters
            </p>

            <button type="button" onClick={handleAnalyze}>
              Analyze Message
            </button>

            {/* Analysis status */}
            {status && <p className="status">{status}</p>}

            {/* Detection results */}
            {status.startsWith("Message analysis") && (
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
                  <p>No matching warning patterns were detected. This does not confirm that the offer is legitimate.</p>
                )}
              </div>
            )}

          </section>

          {/* Display invalid domain information */}
          {domainError && (
            <section className="domain-error">
              <h3>Domain Validation Warning</h3>
              <p>{domainError}</p>
            </section>
          )}

          {/* Show recommendations when available */}
            {recommendations.length > 0 && (
              <section className="recommendations">
                <h3>Recommended Actions</h3>

                <ul>
                  {recommendations.map((recommendation, index) => (
                    <li key={index}>{recommendation}</li>
                  ))}
                </ul>
              </section>
            )}

            {/* Domain comparison results */}
            {domainCheck && (
              <section className="domain-results">
                <h3>Recruiter Domain Analysis</h3>

                <p>
                  <strong>Email domain:</strong>{" "}
                  {domainCheck.email_domain}
                </p>

                <p>
                  <strong>Website domain:</strong>{" "}
                  {domainCheck.website_domain}
                </p>

                <p
                  className={
                    domainCheck.potential_lookalike
                      ? "domain-status domain-lookalike"
                      : "domain-status"
                  }
                >
                  {domainCheck.exact_match
                    ? "Exact domain match"
                    : domainCheck.is_subdomain
                      ? "Related subdomain detected"
                      : domainCheck.potential_lookalike
                        ? "Potential lookalike domain - verify carefully"
                        : "Domains do not match"}
                </p>

                <small>
                  A matching domain does not verify a recruiter's 
                  identity. Confirm the employer's official website
                  independently
                </small>

              </section>
            )}

            {/* Compare email against our company registry */}
            {referenceCheck && (
              <section className="reference-results">
                <h3>Company Reference Check</h3>

                <p>
                  <strong>Recruiter domain:</strong>{" "}
                  {referenceCheck.email_domain}
                </p>

                <p>
                  <strong>Reference domain:</strong>{" "}
                  {referenceCheck.reference_domain}
                </p>

                <p>
                  {referenceCheck.matches_reference
                    ? "Domain matches our demostration reference."
                    : "Domain does not match our demostration reference."}
                </p>

                <small>
                  Demostration data only. This comparison
                  does not verify the recruiter or company.
                </small>
              </section>
            )}


            {/* Show the source behind our company reference */}
            {referenceRecord && (
              <section className="reference-source">
                <h3>Company Reference Source</h3>

                <p>
                  <strong>Domain:</strong> {referenceRecord.domain}
                </p>

                <p>
                  <strong>Source:</strong> {referenceRecord.source}
                </p>

                <p>
                  <strong>Reference status:</strong>{" "}
                  {referenceRecord.verified
                    ? "Company-domain reference documented"
                    : "Demonstration data only"}
                </p>

                {referenceRecord.checked_at && (
                  <p>
                    <strong>Recorded check date:</strong>{" "}
                    {referenceRecord.checked_at}
                  </p>
                )}

                <small>
                  A documented company domain does not verify
                  a recruiter, email sender, or job offer.
                </small>
              </section>
            )}

        </>
      )}

      {activeSection === "posting" && (
        <>
          <section className="posting-analysis">
            <h3>Job Posting Analysis</h3>

            <p>
              Analyze a job advertisement using our experimental
              machine learning model and warning rules.
            </p>

            <input
              type="text"
              placeholder="Job title"
              value={postingTitle}
              onChange={(e) => setPostingTitle(e.target.value)}
            />

            <textarea
              placeholder="Paste the job description here..."
              value={postingDescription}
              onChange={(e) => setPostingDescription(e.target.value)}
              rows={6}
            />

            <button
              type="button"
              onClick={handleAnalyzePosting}
              disabled={checkingPosting}
            >
              {checkingPosting ? "Analyzing..." : "Analyze Posting"}
            </button>

            {postingError && <p role="alert">{postingError}</p>}

            {postingResult && (
              <div className="posting-results">
                <h4>
                  {postingResult.review_recommended
                    ? "Manual Review Recommended"
                    : "No Matching Warnings Detected"}
                </h4>

                {/* Explain why the posting was flagged */}
                <p className="analysis-explanation">
                  {postingResult.prediction === 1 && 
                  postingResult.rule_signals.length > 0
                    ? "Both detection methods found warning patterns."
                    : postingResult.prediction === 1
                    ? "The ML model flagged this posting for review."
                    : postingResult.rule_signals.length > 0
                    ? "Rule-based checks found a warning that the ML model did not flag."
                    : "Neither detection method found matching warning patterns."}
                </p>

                <p>
                  ML result:{" "}
                  {postingResult.prediction === 1
                    ? "Flagged for review"
                    : "Not flagged by ML"}
                </p>

                <p>
                  Model score: {postingResult.model_score.toFixed(3)}
                </p>

                <p>
                  Decision threshold: {postingResult.threshold}
                </p>

                <h4>Rule-Based Findings</h4>

                {postingResult.rule_signals.length > 0 ? (
                  <ul>
                    {postingResult.rule_signals.map((signal, index) => (
                      <li key={index}>{signal}</li>
                    ))}
                  </ul>
                ) : (
                  <p>No matching rule-based warnings.</p>
                )}

                <small>
                  Experimental model trained on historical job postings.
                  The score is not a verified probability of fraud.
                  Results cannot confirm whether an offer is legitimate.
                </small>
              </div>
            )}
          </section>
        
        </>
      )}

      {activeSection === "tools" && (
        <>
            {/* Request domain registration information */}
            <section className="registration-section">
              <h3>Domain Registration Check</h3>

              <div className="company-fields">
                <label htmlFor="registration-company-name">Company Name</label>
                <input
                  id="registration-company-name"
                  type="text"
                  placeholder="Enter company name"
                  value={companyName}
                  onChange={(event) => setCompanyName(event.target.value)}
                />
              </div>

              <button
                type="button"
                onClick={handleCheckDomain}
                disabled={checkingDomain || !companyName.trim()}
              >
                {checkingDomain ? "Checking..." : "Check Registration"}
              </button>

              {registration && (
                <div className="registration-result">
                  {registration.status === "checked" ? (
                    <>
                      <p>Domain: {registration.domain}</p>
                      <p>
                        Registration date:{" "}
                        {registration.registered_at ?? "Not available"}
                      </p>
                    </>
                  ) : (
                    <p>
                      {registration.status === "no-reference"
                        ? "No documented company reference available"
                        : "Registration information is currently unavailable."}
                    </p>
                  )}
                </div>
              )}

              <small>
                Domain registration information does not verify 
                the company, recruiter, or job offer.
              </small>

            </section>
      
          {/* Suspicious URL analysis */}
          <section className="url-analysis-section">
            <h3>Suspicious URL Analysis</h3>

            <p>
              Check a job-related link for common warning signs.
            </p>

            <input
              type="url"
              placeholder="https://example.com/jobs"
              value={jobUrl}
              onChange={(event) => setJobUrl(event.target.value)}
              aria-label="Job-related URL"
            />
        
            <button
              type="button"
              onClick={handleAnalyzeUrl}
              disabled={checkingUrl}
            >
              {checkingUrl ? "Checking..." : "Analyze URL"}
            </button>

            {urlError && <p role="alert">{urlError}</p>}

            {urlResult && (
              <div className="url-results">
                <h4>URL Analysis Results</h4>

                {urlResult.hostname && (
                  <p>Hostname: {urlResult.hostname}</p>
                )}

                {urlResult.signals.length > 0 ? (
                  <ul>
                    {urlResult.signals.map((signal, index) => (
                      <li key={index}>{signal}</li>
                    ))}
                  </ul>
                ) : (
                  <p>No matching URL warning patterns detected.</p>
                )}
              </div>
            )}
            <small>
              This check does not visit the URL or guarantee it is safe.
            </small>
          </section>

        </>
      )}

      <footer>
        Proofline help identify warning signs 
        It does not verify job offers.
      </footer>
    </main>
  );
}

export default App;