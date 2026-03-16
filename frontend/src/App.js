import React, { useState } from "react";

function App() {

  // AI SERVER IP (Linux server)
  const API = "http://192.168.20.200:8000";

  const [file, setFile] = useState(null);
  const [downloadLink, setDownloadLink] = useState(null);
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [debugImages, setDebugImages] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);

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

      // Load debug images (AI bounding box preview)
      try {
        const debugResponse = await fetch(`${API}/debug/${data.site}`);
        const debugData = await debugResponse.json();
        setDebugImages(debugData.debug_images || []);
        setCurrentIndex(0);
      } catch {
        setDebugImages([]);
      }

    } catch (error) {

      alert("Upload failed. Check if the AI server is running.");

    }

    setLoading(false);
  };

  return (

    <div style={{
      textAlign: "center",
      marginTop: "60px",
      fontFamily: "Arial"
    }}>

      <h1>Telkha Vision AI</h1>
      <p>Telecom Survey Photo Auto-Sorter</p>

      {/* Upload section */}

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

      {/* Processing indicator */}

      {loading && (
        <div>
          <p>AI processing in progress...</p>
        </div>
      )}

      {/* AI REPORT DASHBOARD */}

      {report && (

        <div style={{
          marginTop: "30px",
          border: "1px solid #ddd",
          padding: "20px",
          width: "500px",
          marginLeft: "auto",
          marginRight: "auto",
          borderRadius: "10px",
          backgroundColor: "#fafafa"
        }}>

          <h2>Sorting Summary</h2>

          <p><b>Total Photos:</b> {report.total_images}</p>
          <p><b>Sorted:</b> {report.sorted_images}</p>
          <p><b>Unsorted:</b> {report.unsorted_images}</p>

          <hr />

          <h3>Detected Equipment</h3>

          {Object.keys(report.class_counts).length === 0 ? (
            <p>No equipment detected</p>
          ) : (

            Object.keys(report.class_counts).map((key) => (

              <div key={key} style={{
                display: "flex",
                justifyContent: "space-between",
                borderBottom: "1px solid #eee",
                padding: "5px"
              }}>

                <span>{key}</span>

                <span>
                  {report.class_counts[key]} detections
                </span>

              </div>

            ))

          )}

          <hr />

          {/* CLASS CONFIDENCE */}

          {report.class_confidence && (

            <>
              <h3>AI Confidence</h3>

              {Object.keys(report.class_confidence).map((key) => (

                <div key={key} style={{
                  display: "flex",
                  justifyContent: "space-between",
                  borderBottom: "1px solid #eee",
                  padding: "5px"
                }}>

                  <span>{key}</span>

                  <span>
                    {(report.class_confidence[key] * 100).toFixed(1)} %
                  </span>

                </div>

              ))}

            </>

          )}

        </div>

      )}

      {/* AI DETECTION PREVIEW */}

      {debugImages.length > 0 && (

        <div style={{
          marginTop: "40px",
          width: "900px",
          marginLeft: "auto",
          marginRight: "auto"
        }}>

          <h2>AI Detection Preview</h2>

          <div style={{
            display: "flex",
            justifyContent: "center",
            gap: "10px",
            flexWrap: "wrap"
          }}>

            {debugImages.slice(currentIndex, currentIndex + 5).map((img, i) => (

              <img
                key={i}
                src={`${API}${img}`}
                alt="AI detection"
                style={{
                  width: "160px",
                  border: "1px solid #ccc",
                  borderRadius: "6px"
                }}
              />

            ))}

          </div>

          <br />

          <button
            onClick={() => setCurrentIndex(Math.max(currentIndex - 5, 0))}
          >
            ◀ Previous
          </button>

          <button
            onClick={() => setCurrentIndex(currentIndex + 5)}
            style={{ marginLeft: "10px" }}
          >
            Next ▶
          </button>

        </div>

      )}

      <br />

      {/* DOWNLOAD BUTTON */}

      {downloadLink && (

        <a href={downloadLink}>

          <button style={{
            padding: "10px 20px",
            fontSize: "16px"
          }}>
            Download Sorted Results
          </button>

        </a>

      )}

    </div>
  );
}

export default App;