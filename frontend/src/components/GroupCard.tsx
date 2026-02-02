import React from 'react';
import { Users, Trash2, Settings } from 'lucide-react';
import { Group } from '../types';

interface GroupCardProps {
  group: Group;
  onClick?: () => void;
  onDelete?: (id: number) => void;
  onManage?: (id: number) => void;
}

export const GroupCard: React.FC<GroupCardProps> = ({ group, onClick, onDelete, onManage }) => {
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onDelete) {
      onDelete(group.id);
    }
  };

  const handleManage = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (onManage) {
      onManage(group.id);
    }
  };

  return (
    <div
      onClick={onClick}
      className={`bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900 p-4 ${
        onClick ? 'hover:shadow-lg dark:hover:shadow-gray-800 cursor-pointer' : ''
      } transition-shadow`}
    >
      <div className="flex items-start justify-between">
        <div className="flex items-start space-x-3 flex-1">
          <Users className="w-8 h-8 text-blue-600 dark:text-blue-400" />
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{group.name}</h3>
            {group.description && (
              <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{group.description}</p>
            )}
            <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
              {group.display_count} {group.display_count === 1 ? 'display' : 'displays'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {onManage && (
            <button
              onClick={handleManage}
              className="p-2 text-blue-600 dark:text-blue-400 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
              title="Manage displays"
            >
              <Settings className="w-5 h-5" />
            </button>
          )}
          {onDelete && (
            <button
              onClick={handleDelete}
              className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
              title="Delete group"
            >
              <Trash2 className="w-5 h-5" />
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
