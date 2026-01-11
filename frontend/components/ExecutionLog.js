import React, { useState, useEffect } from 'react';
import { useStore } from '../helpers/store';

const ExecutionLog = () => {
  const { executionLogs } = useStore();
  const [visible, setVisible] = useState(false);

  // Automatically show the log window when new logs arrive
  useEffect(() => {
    if (executionLogs && executionLogs.length > 0) {
      setVisible(true);
    }
  }, [executionLogs]);

  if (!visible || !executionLogs || executionLogs.length === 0) {
    return null;
  }

  return (
    <div className="execution-log-window">
      <div className="execution-log-header">
        <span>Execution Log</span>
        <button className="close-log-button" onClick={() => setVisible(false)}>&times;</button>
      </div>
      <div className="execution-log-content">
        {executionLogs.map((log, index) => (
          <div key={index} className="log-entry">
            {log}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ExecutionLog;