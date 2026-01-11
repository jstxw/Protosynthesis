import React from 'react';
import { LucideIcon } from 'lucide-react';

interface NodeCardProps {
  title: string;
  typeBadge?: string;
  icon?: LucideIcon;
  headerColorClass?: string;
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  onClick?: () => void;
  width?: string;
}

export const NodeCard = ({
  title,
  typeBadge,
  icon: Icon,
  headerColorClass = 'node-header-start',
  children,
  className = '',
  style = {},
  onClick,
  width = '320px'
}: NodeCardProps) => {
  return (
    <div
      className={`ui-node ${className}`}
      style={{ width, maxWidth: '100%', ...style }}
      onClick={onClick}
    >
      {/* Icon Nub */}
      {Icon && (
        <div className={`node-icon-nub ${headerColorClass}`} style={{ top: '-25px' }}>
          <Icon className="node-nub-icon" size={24} />
        </div>
      )}

      {/* Header */}
      <div className={`node-header ${headerColorClass}`}>
        <h3 style={{ fontWeight: 'bold', fontSize: '12px', margin: 0, color: 'inherit' }}>{title}</h3>
        {typeBadge && <span className="node-type" style={{ fontSize: '10px', opacity: 0.8 }}>{typeBadge}</span>}
      </div>

      {/* Body */}
      <div className="node-body" style={{ padding: '10px', fontSize: '12px', fontWeight: 'bold' }}>
        {children}
      </div>
    </div>
  );
};

