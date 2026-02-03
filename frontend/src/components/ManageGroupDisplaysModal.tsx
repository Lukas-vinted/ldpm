import { useState, useMemo } from 'react';
import { X, Plus, Trash2, CheckSquare, Square, Filter } from 'lucide-react';
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
  const [locationFilter, setLocationFilter] = useState<string>('all');
  const { data: allDisplays } = useDisplays();
  const addMutation = useAddDisplaysToGroup();
  const removeMutation = useRemoveDisplaysFromGroup();

  const availableDisplays = allDisplays?.filter(d => !currentDisplayIds.includes(d.id)) || [];
  const currentDisplays = allDisplays?.filter(d => currentDisplayIds.includes(d.id)) || [];

  const uniqueLocations = useMemo(() => {
    const locations = new Set(availableDisplays.map(d => d.location).filter(Boolean));
    return Array.from(locations).sort();
  }, [availableDisplays]);

  const filteredDisplays = useMemo(() => {
    if (locationFilter === 'all') return availableDisplays;
    return availableDisplays.filter(d => d.location === locationFilter);
  }, [availableDisplays, locationFilter]);

  if (!isOpen || !group) return null;

  const handleToggleSelection = (displayId: number) => {
    setSelectedDisplayIds(prev =>
      prev.includes(displayId)
        ? prev.filter(id => id !== displayId)
        : [...prev, displayId]
    );
  };

  const handleSelectAll = () => {
    const allFilteredIds = filteredDisplays.map(d => d.id);
    setSelectedDisplayIds(allFilteredIds);
  };

  const handleClearSelection = () => {
    setSelectedDisplayIds([]);
  };

  const handleSelectByLocation = (location: string) => {
    const locationDisplayIds = availableDisplays
      .filter(d => d.location === location)
      .map(d => d.id);
    setSelectedDisplayIds(prev => {
      const newIds = [...prev];
      locationDisplayIds.forEach(id => {
        if (!newIds.includes(id)) {
          newIds.push(id);
        }
      });
      return newIds;
    });
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
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  Available Displays ({filteredDisplays.length})
                </h3>
              </div>

              {/* Bulk Selection Toolbar */}
              <div className="mb-4 space-y-3">
                {/* Location Filter */}
                {uniqueLocations.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      <Filter className="w-4 h-4 inline mr-1" />
                      Filter by Location
                    </label>
                    <select
                      value={locationFilter}
                      onChange={(e) => setLocationFilter(e.target.value)}
                      className="w-full px-3 py-2 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="all">All Locations ({availableDisplays.length})</option>
                      {uniqueLocations.map(location => (
                        <option key={location} value={location}>
                          {location} ({availableDisplays.filter(d => d.location === location).length})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {/* Bulk Action Buttons */}
                <div className="flex gap-2">
                  <button
                    onClick={handleSelectAll}
                    disabled={filteredDisplays.length === 0}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <CheckSquare className="w-4 h-4" />
                    Select All {locationFilter !== 'all' ? 'Filtered' : ''}
                  </button>
                  <button
                    onClick={handleClearSelection}
                    disabled={selectedDisplayIds.length === 0}
                    className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Square className="w-4 h-4" />
                    Clear Selection
                  </button>
                </div>

                {/* Quick Location Buttons */}
                {uniqueLocations.length > 1 && uniqueLocations.length <= 5 && (
                  <div className="flex flex-wrap gap-2">
                    {uniqueLocations.map(location => {
                      const count = availableDisplays.filter(d => d.location === location).length;
                      return (
                        <button
                          key={location}
                          onClick={() => handleSelectByLocation(location)}
                          className="flex items-center gap-1 px-3 py-1.5 text-xs bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors"
                        >
                          <Plus className="w-3 h-3" />
                          Add all from {location.split(' ').pop()} ({count})
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>

              {availableDisplays.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400 text-sm">All displays are already in this group</p>
              ) : filteredDisplays.length === 0 ? (
                <p className="text-gray-500 dark:text-gray-400 text-sm">No displays match the selected filter</p>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {filteredDisplays.map((display) => (
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
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {display.location || 'No location'} • {display.ip_address}
                        </p>
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
