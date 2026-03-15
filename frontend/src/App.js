import React, { useState } from "react";

function App() {

  const [file, setFile] = useState(null);
  const [downloadLink, setDownloadLink] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleUpload = async () => {

    if (!file) {
      alert("Please select a ZIP file");
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);

    try {

      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData
      });

      const data = await response.json();

      setDownloadLink(`http://localhost:8000${data.download}`);

    } catch (error) {

      alert("Upload failed");

    }

    setLoading(false);
  };

  return (

    <div style={{textAlign:"center", marginTop:"80px"}}>

      <h1>Telkha Vision AI</h1>
      <p>Upload Telecom Survey Photos</p>

      <input
        type="file"
        accept=".zip"
        onChange={(e) => setFile(e.target.files[0])}
      />

      <br/><br/>

      <button onClick={handleUpload}>
        Upload and Process
      </button>

      <br/><br/>

      {loading && (
        <div>
          <p>Processing... please wait</p>
          <div className="spinner"></div>
        </div>
      )}

      {downloadLink && (
        <a href={downloadLink}>
          <button>Download Sorted Results</button>
        </a>
      )}

    </div>
  );
}

export default App;