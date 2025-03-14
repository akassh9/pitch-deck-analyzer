import React from 'react';

interface TemplateSelectorProps {
  selectedTemplate: string;
  onTemplateChange: (template: string) => void;
}

const templates = [
  { id: 'default', name: 'Default', description: 'Balanced analysis suitable for most pitch decks' },
  { id: 'seed', name: 'Seed Stage', description: 'Focus on team capabilities and early validation' },
  { id: 'seriesa', name: 'Series A', description: 'Emphasis on growth metrics and unit economics' },
  { id: 'growth', name: 'Growth Stage', description: 'Focus on market leadership and scaling' },
];

export function TemplateSelector({ selectedTemplate, onTemplateChange }: TemplateSelectorProps) {
  console.log('TemplateSelector rendering with selectedTemplate:', selectedTemplate);
  
  // Check if the selected template is valid
  const isValidTemplate = templates.some(t => t.id === selectedTemplate);
  console.log('Is valid template:', isValidTemplate);
  
  // If not valid, log a warning
  if (!isValidTemplate) {
    console.warn(`Warning: Selected template "${selectedTemplate}" is not in the valid templates list`);
  }
  
  return (
    <div className="space-y-4">
      <label className="block text-lg font-serif">Select Template</label>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {templates.map((template) => (
          <div
            key={template.id}
            className={`p-4 rounded-lg border cursor-pointer transition-colors ${
              selectedTemplate === template.id
                ? 'border-primary bg-primary/10'
                : 'border-border hover:border-primary/50'
            }`}
            onClick={() => {
              console.log(`Template selected: ${template.id}`);
              onTemplateChange(template.id);
            }}
          >
            <h3 className="font-serif text-lg mb-1">{template.name}</h3>
            <p className="text-sm text-muted-foreground">{template.description}</p>
          </div>
        ))}
      </div>
    </div>
  );
} 