import React, { useState } from "react";

function App() {

  // Linux AI server
  const API = "http://192.168.20.200:8000";

  const [file, setFile] = useState(null);
  const [downloadLink, setDownloadLink] = useState(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);

  const handleUpload = async () => {

    if (!file) {
      alert("Please select a ZIP or RAR file");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setReport(null);
    setDownloadLink(null);

    try {

      const response = await fetch(`${API}/upload`, {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      if (data.error) {
        alert(data.error);
        setLoading(false);
        return;
      }

      setDownloadLink(`${API}${data.download}`);
      setReport(data.report);

    } catch (error) {

      alert("Upload failed. Check if the AI server is running.");

    }

    setLoading(false);
  };

  return (

    <div style={{
      textAlign: "center",
      marginTop: "80px",
      fontFamily: "Arial"
    }}>

      <h1>Telkha Vision AI</h1>
      <p>Telecom Survey Photo Auto-Sorter</p>

      {/* Upload input */}

      <input
        type="file"
        accept=".zip,.rar"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <br /><br />

      <button onClick={handleUpload}>
        Upload and Process
      </button>

      <br /><br />

      {/* Loading message */}

      {loading && (
        <div>
          <p>Processing photos... please wait</p>
        </div>
      )}

      {/* AI report */}

      {report && (
        <div style={{
          marginTop: "30px",
          border: "1px solid #ddd",
          padding: "20px",
          width: "420px",
          marginLeft: "auto",
          marginRight: "auto",
          borderRadius: "8px",
          backgroundColor: "#fafafa"
        }}>

          <h2>Sorting Result</h2>

          <p><b>Total Photos:</b> {report.total_images}</p>
          <p><b>Sorted:</b> {report.sorted_images}</p>
          <p><b>Unsorted:</b> {report.unsorted_images}</p>

          <h3>Detected Equipment</h3>

          {Object.keys(report.class_counts).length === 0 ? (
            <p>No equipment detected</p>
          ) : (
            Object.keys(report.class_counts).map((key) => (
              <p key={key}>
                {key} : {report.class_counts[key]}
              </p>
            ))
          )}

        </div>
      )}

      <br />

      {/* Download button */}

      {downloadLink && (
        <a href={downloadLink}>
          <button>
            Download Sorted Results
          </button>
        </a>
      )}

    </div>
  );
}

export default App;