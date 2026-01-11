import React, { useRef } from 'react';
import { useStore } from '../helpers/store';
import Image from 'next/image';

const TopBar = () => {
  const { executeGraph, saveProject, loadProject } = useStore();
  const fileInputRef = useRef(null);

  const handleLoadClick = () => {
    fileInputRef.current.click();
  };

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const projectData = JSON.parse(e.target.result);
        loadProject(projectData);
      } catch (error) {
        console.error("Error parsing project file:", error);
        alert("Invalid project file. Please select a valid JSON file.");
      }
    };
    reader.readAsText(file);
  };

  return (
    <header className="top-bar">
      <div className="top-bar-buttons">
        <button onClick={saveProject} title="Save Project">
          <Image src="/save.svg" alt="Save" width={20} height={20} />
        </button>
        <button onClick={handleLoadClick} title="Load Project">
          <Image src="/load.svg" alt="Load" width={20} height={20} />
        </button>
        <input
          type="file"
          ref={fileInputRef}
          style={{ display: 'none' }}
          onChange={handleFileChange}
          accept=".json,application/json"
        />
        <button onClick={executeGraph} className="execute-button" title="Run Graph">
          <Image src="/play.svg" alt="Run" width={20} height={20} />
          <span>Run</span>
        </button>
      </div>
    </header>
  );
};

export default TopBar;