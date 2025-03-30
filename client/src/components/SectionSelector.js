import React from 'react';

const SectionSelector = ({ sections, currentSection, onSectionChange }) => {
  return (
    <div className="section-selector">
      {sections.map((section) => (
        <button
          key={section}
          className={currentSection === section ? 'active' : ''}
          onClick={() => onSectionChange(section)}
        >
          {section === 'all' ? 'All Sections' : section}
        </button>
      ))}
    </div>
  );
};

export default SectionSelector;
