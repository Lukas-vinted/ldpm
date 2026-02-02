import { useState } from 'react';
import { X, Plus, Trash2 } from 'lucide-react';
import { useDisplays, useAddDisplaysToGroup, useRemoveDisplaysFromGroup } from '../hooks/useApi';
import { Group } from '../types';

interface ManageGroupDisplaysModalProps {
  isOpen: boolean;
  onClose: () => void;
  group: Group | null;
  currentDisplayIds: number[];
}

export function ManageGroupDisplaysModal({ isOpen, onClose, group, currentDisplayIds }: ManageGroupDisplaysModalProps) {
  const [selectedDisplayIds, setSelectedDisplayIds] = useState<number[]>([]);
  const { data: allDisplays } = useDisplays();
  const addMutation = useAddDisplaysToGroup();
  const removeMutation = useRemoveDisplaysFromGroup();

  if (!isOpen || !group) return null;

  const availableDisplays = allDisplays?.filter(d => !currentDisplayIds.includes(d.id)) || [];
  const currentDisplays = allDisplays?.filter(d => currentDisplayIds.includes(d.id)) || [];

  const handleToggleSelection = (displayId: number) => {
    setSelectedDisplayIds(prev =>
      prev.includes(displayId)
        ? prev.filter(id => id !== displayId)
        : [...prev, displayId]
    );
  };

  const handleAddDisplays = async () => {
    if (selectedDisplayIds.length === 0) return;
    
    await addMutation.mutateAsync({
      groupId: group.id,
      displayIds: selectedDisplayIds
    });
    
    setSelectedDisplayIds([]);
  };

  const handleRemoveDisplay = async (displayId: number) => {
    await removeMutation.mutateAsync({
      groupId: group.id,
      displayIds: [displayId]
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        <div className="flex justify-between items-center p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
            Manage Displays - {group.name}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 overflow-y-auto max-h-[calc(90vh-180px)]">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Available Displays ({availableDisplays.length})
              </h3>
              {availableDisplays.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400 text-sm">All displays are already in this group</p>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {availableDisplays.map((display) => (
                    <label
                      key={display.id}
                      className="flex items-center p-3 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 cursor-pointer transition-colors"
                    >
                      <input
                        type="checkbox"
                        checked={selectedDisplayIds.includes(display.id)}
                        onChange={() => handleToggleSelection(display.id)}
                        className="w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                      />
                      <div className="ml-3 flex-1">
                        <p className="font-medium text-gray-900 dark:text-white">{display.name}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{display.ip_address}</p>
                      </div>
                    </label>
                  ))}
                </div>
              )}
              {selectedDisplayIds.length > 0 && (
                <button
                  onClick={handleAddDisplays}
                  disabled={addMutation.isPending}
                  className="mt-4 w-full flex items-center justify-center gap-2 px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  <Plus className="w-5 h-5" />
                  Add {selectedDisplayIds.length} Display{selectedDisplayIds.length > 1 ? 's' : ''}
                </button>
              )}
            </div>

            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                Current Displays ({currentDisplays.length})
              </h3>
              {currentDisplays.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400 text-sm">No displays in this group yet</p>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {currentDisplays.map((display) => (
                    <div
                      key={display.id}
                      className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                    >
                      <div className="flex-1">
                        <p className="font-medium text-gray-900 dark:text-white">{display.name}</p>
                        <p className="text-sm text-gray-500 dark:text-gray-400">{display.ip_address}</p>
                      </div>
                      <button
                        onClick={() => handleRemoveDisplay(display.id)}
                        disabled={removeMutation.isPending}
                        className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors disabled:opacity-50"
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="flex justify-end gap-3 p-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={onClose}
            className="px-6 py-2 text-gray-700 dark:text-gray-300 bg-gray-200 dark:bg-gray-700 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
