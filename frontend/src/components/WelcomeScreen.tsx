import React from 'react';
import { Database, BarChart3, GitBranch, TrendingUp, PieChart, Package } from 'lucide-react';
import './WelcomeScreen.css';

interface Props {
  onSelectQuery: (query: string) => void;
}

const suggestions = [
  { text: "Show me the top 5 products by revenue", icon: BarChart3, category: "Analytics" },
  { text: "Draw the ER diagram for this database", icon: GitBranch, category: "Diagrams" },
  { text: "What's the monthly sales trend?", icon: TrendingUp, category: "Insights" },
  { text: "Create a flowchart of the order process", icon: Database, category: "Diagrams" },
  { text: "Which category generates the most revenue?", icon: PieChart, category: "Analytics" },
  { text: "Show inventory levels vs sales", icon: Package, category: "Insights" }
];

export const WelcomeScreen: React.FC<Props> = ({ onSelectQuery }) => {
  return (
    <div className="welcome-container">
      <div className="welcome-background-glow"></div>
      <div className="welcome-grid-pattern"></div>
      
      <div className="welcome-header">
        <h1 className="welcome-logo">DataChat AI</h1>
        <div className="welcome-subtitle-wrapper">
          <p className="welcome-subtitle">Ask questions about your data in plain English</p>
        </div>
        <p className="welcome-tagline">Powered by AI &middot; Ask anything about your database</p>
      </div>
      
      <div className="suggestions-grid">
        {suggestions.map((suggestion, i) => {
          const Icon = suggestion.icon;
          return (
            <div 
              key={i} 
              className={`suggestion-card stagger-${i + 1}`} 
              onClick={() => onSelectQuery(suggestion.text)}
            >
              <div className="suggestion-icon-wrapper">
                <Icon className="suggestion-icon" size={24} />
              </div>
              <div className="suggestion-content">
                <span className="suggestion-category">{suggestion.category}</span>
                <p className="suggestion-text">{suggestion.text}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};