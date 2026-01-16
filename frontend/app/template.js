'use client';

import { useEffect, useState } from 'react';

export default function Template({ children }) {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  return (
    <div
      style={{
        opacity: isVisible ? 1 : 0,
        transition: 'opacity 0.6s ease-in-out'
      }}
    >
      {children}
    </div>
  );
}
