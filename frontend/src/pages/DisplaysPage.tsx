import { useState, useEffect, useMemo } from 'react';
import { Plus, Upload, LayoutGrid, List, ChevronDown } from 'lucide-react';
import { DisplayCard } from '../components';
import { AddDisplayModal } from '../components/AddDisplayModal';
import { ImportCSVModal } from '../components/ImportCSVModal';
import { ConfirmDeleteModal } from '../components/ConfirmDeleteModal';
import { useDisplays, usePowerControl, useDeleteDisplay } from '../hooks/useApi';
import { useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Display } from '../types';
import { StatusBadge } from '../components/StatusBadge';
import { PowerButton } from '../components/PowerButton';

type FilterType = 'all' | 'online' | 'offline' | 'standby' | 'unknown';
type SortType = 'name-asc' | 'name-desc' | 'id-asc' | 'id-desc' | 'status';
type ViewMode = 'tiles' | 'details';

export default function DisplaysPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: number; name: string } | null>(null);
  const [filter, setFilter] = useState<FilterType>('all');
  const [sort, setSort] = useState<SortType>('name-asc');
  const [viewMode, setViewMode] = useState<ViewMode>('tiles');
  const [sortDropdownOpen, setSortDropdownOpen] = useState(false);
  const { data: displays, isLoading, error } = useDisplays();
  const queryClient = useQueryClient();
  const powerMutation = usePowerControl();
  const deleteMutation = useDeleteDisplay();

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const { data } = await apiClient.get<Display[]>('/displays?fetch_status=true');
        queryClient.setQueryData(['displays'], data);
      } catch (err) {
        console.error('Failed to fetch display status:', err);
      }
    };

    const timer = setTimeout(() => {
      fetchStatus();
    }, 500);

    return () => clearTimeout(timer);
  }, [queryClient]);

  useEffect(() => {
    const handleClickOutside = () => setSortDropdownOpen(false);
    if (sortDropdownOpen) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [sortDropdownOpen]);

  const filteredAndSortedDisplays = useMemo(() => {
    if (!displays) return [];

    let filtered = displays;
    if (filter !== 'all') {
      filtered = displays.filter((display) => {
        switch (filter) {
          case 'online':
            return display.status === 'active';
          case 'offline':
            return display.status === 'error' || display.status === 'offline';
          case 'standby':
            return display.status === 'standby';
          case 'unknown':
            return display.status === 'unknown';
          default:
            return true;
        }
      });
    }

    const sorted = [...filtered].sort((a, b) => {
      switch (sort) {
        case 'name-asc':
          return a.name.localeCompare(b.name);
        case 'name-desc':
          return b.name.localeCompare(a.name);
        case 'id-asc':
          return a.id - b.id;
        case 'id-desc':
          return b.id - a.id;
        case 'status':
          return a.status.localeCompare(b.status);
        default:
          return 0;
      }
    });

    return sorted;
  }, [displays, filter, sort]);

  const statusCounts = useMemo(() => {
    if (!displays) return { all: 0, online: 0, offline: 0, standby: 0, unknown: 0 };
    
    return {
      all: displays.length,
      online: displays.filter(d => d.status === 'active').length,
      offline: displays.filter(d => d.status === 'error' || d.status === 'offline').length,
      standby: displays.filter(d => d.status === 'standby').length,
      unknown: displays.filter(d => d.status === 'unknown').length,
    };
  }, [displays]);

  const handlePowerToggle = (id: number, state: 'on' | 'off') => {
    powerMutation.mutate({ id, state });
  };

  const handleDeleteClick = (id: number) => {
    const display = displays?.find(d => d.id === id);
    if (display) {
      setDeleteConfirm({ id, name: display.name });
    }
  };

  const handleDeleteConfirm = () => {
    if (deleteConfirm) {
      deleteMutation.mutate(deleteConfirm.id, {
        onSuccess: () => {
          setDeleteConfirm(null);
        },
      });
    }
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="text-gray-500 dark:text-gray-400">Loading displays...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg p-4">
        <p className="text-red-800 dark:text-red-300">Failed to load displays. Please try again.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Displays</h2>
        <div className="flex space-x-3">
          <button 
            onClick={() => setIsImportModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Upload className="w-5 h-5" />
            <span>Import CSV</span>
          </button>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            <span>Add Display</span>
          </button>
        </div>
      </div>

      <div className="flex justify-between items-center mb-6 bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900 p-4">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              filter === 'all'
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            All ({statusCounts.all})
          </button>
          <button
            onClick={() => setFilter('online')}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              filter === 'online'
                ? 'bg-green-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            Online ({statusCounts.online})
          </button>
          <button
            onClick={() => setFilter('offline')}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              filter === 'offline'
                ? 'bg-red-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            Offline ({statusCounts.offline})
          </button>
          <button
            onClick={() => setFilter('standby')}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              filter === 'standby'
                ? 'bg-yellow-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            Standby ({statusCounts.standby})
          </button>
          <button
            onClick={() => setFilter('unknown')}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              filter === 'unknown'
                ? 'bg-gray-600 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            }`}
          >
            Unknown ({statusCounts.unknown})
          </button>
        </div>

        <div className="flex items-center space-x-3">
          <div className="relative">
            <button
              onClick={(e) => { e.stopPropagation(); setSortDropdownOpen(!sortDropdownOpen); }}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              <span className="text-sm font-medium">Sort</span>
              <ChevronDown className="w-4 h-4" />
            </button>
            
            {sortDropdownOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-lg shadow-lg dark:shadow-gray-900 border border-gray-200 dark:border-gray-700 z-10">
                <button
                  onClick={() => { setSort('name-asc'); setSortDropdownOpen(false); }}
                  className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 ${
                    sort === 'name-asc' ? 'text-blue-600 dark:text-blue-400 font-medium' : 'text-gray-700 dark:text-gray-300'
                  }`}
                >
                  Name (A-Z)
                </button>
                <button
                  onClick={() => { setSort('name-desc'); setSortDropdownOpen(false); }}
                  className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 ${
                    sort === 'name-desc' ? 'text-blue-600 dark:text-blue-400 font-medium' : 'text-gray-700 dark:text-gray-300'
                  }`}
                >
                  Name (Z-A)
                </button>
                <button
                  onClick={() => { setSort('id-asc'); setSortDropdownOpen(false); }}
                  className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 ${
                    sort === 'id-asc' ? 'text-blue-600 dark:text-blue-400 font-medium' : 'text-gray-700 dark:text-gray-300'
                  }`}
                >
                  ID (Low to High)
                </button>
                <button
                  onClick={() => { setSort('id-desc'); setSortDropdownOpen(false); }}
                  className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 ${
                    sort === 'id-desc' ? 'text-blue-600 dark:text-blue-400 font-medium' : 'text-gray-700 dark:text-gray-300'
                  }`}
                >
                  ID (High to Low)
                </button>
                <button
                  onClick={() => { setSort('status'); setSortDropdownOpen(false); }}
                  className={`w-full text-left px-4 py-2 text-sm hover:bg-gray-100 dark:hover:bg-gray-700 rounded-b-lg ${
                    sort === 'status' ? 'text-blue-600 dark:text-blue-400 font-medium' : 'text-gray-700 dark:text-gray-300'
                  }`}
                >
                  Status
                </button>
              </div>
            )}
          </div>

          <div className="flex bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
            <button
              onClick={() => setViewMode('tiles')}
              className={`p-2 rounded transition-colors ${
                viewMode === 'tiles'
                  ? 'bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-400'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
              title="Tiles view"
            >
              <LayoutGrid className="w-5 h-5" />
            </button>
            <button
              onClick={() => setViewMode('details')}
              className={`p-2 rounded transition-colors ${
                viewMode === 'details'
                  ? 'bg-white dark:bg-gray-600 text-blue-600 dark:text-blue-400'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
              }`}
              title="Details view"
            >
              <List className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {!filteredAndSortedDisplays || filteredAndSortedDisplays.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900 p-8 text-center">
          <p className="text-gray-600 dark:text-gray-400">
            {!displays || displays.length === 0 
              ? 'No displays configured yet. Add displays to get started.'
              : 'No displays match the selected filter.'}
          </p>
        </div>
      ) : viewMode === 'tiles' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredAndSortedDisplays.map((display) => (
            <DisplayCard
              key={display.id}
              display={display}
              onPowerToggle={handlePowerToggle}
              onDelete={handleDeleteClick}
              isLoading={powerMutation.isPending}
            />
          ))}
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow dark:shadow-gray-900 overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  IP Address
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Location
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {filteredAndSortedDisplays.map((display) => (
                <tr key={display.id} className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900 dark:text-white">{display.name}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500 dark:text-gray-400">{display.ip_address}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-500 dark:text-gray-400">{display.location || '-'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={display.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex items-center justify-end space-x-2">
                      <PowerButton
                        isOn={display.status === 'active'}
                        isLoading={powerMutation.isPending}
                        onToggle={() => handlePowerToggle(display.id, display.status === 'active' ? 'off' : 'on')}
                      />
                      <button
                        onClick={() => handleDeleteClick(display.id)}
                        className="p-2 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                        title="Delete display"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                        </svg>
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <AddDisplayModal 
        isOpen={isModalOpen} 
        onClose={() => setIsModalOpen(false)} 
      />

      <ImportCSVModal 
        isOpen={isImportModalOpen} 
        onClose={() => setIsImportModalOpen(false)} 
      />

      <ConfirmDeleteModal
        isOpen={!!deleteConfirm}
        onClose={() => setDeleteConfirm(null)}
        onConfirm={handleDeleteConfirm}
        title="Delete Display"
        message="Are you sure you want to delete this display?"
        itemName={deleteConfirm?.name}
        isDeleting={deleteMutation.isPending}
      />
    </div>
  );
}
