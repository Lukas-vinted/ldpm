import React from 'react';
import { Users } from 'lucide-react';
import { Group } from '../types';

interface GroupCardProps {
  group: Group;
  onClick?: () => void;
}

export const GroupCard: React.FC<GroupCardProps> = ({ group, onClick }) => {
  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-lg shadow p-4 ${
        onClick ? 'hover:shadow-lg cursor-pointer' : ''
      } transition-shadow`}
    >
      <div className="flex items-start space-x-3">
        <Users className="w-8 h-8 text-blue-600" />
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{group.name}</h3>
          {group.description && (
            <p className="text-sm text-gray-600 mt-1">{group.description}</p>
          )}
          <p className="text-xs text-gray-400 mt-2">
            {group.display_count} {group.display_count === 1 ? 'display' : 'displays'}
          </p>
        </div>
      </div>
    </div>
  );
};
