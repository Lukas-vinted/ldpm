import React from 'react';
import { Power } from 'lucide-react';

interface PowerButtonProps {
  isOn: boolean;
  isLoading?: boolean;
  onToggle: () => void;
}

export const PowerButton: React.FC<PowerButtonProps> = ({ isOn, isLoading = false, onToggle }) => {
  return (
    <button
      onClick={onToggle}
      disabled={isLoading}
      className={`p-2 rounded-lg transition-colors ${
        isLoading ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-100'
      }`}
      title={isOn ? 'Power Off' : 'Power On'}
    >
      <Power className={`w-5 h-5 ${isOn ? 'text-green-600' : 'text-gray-400'}`} />
    </button>
  );
};
