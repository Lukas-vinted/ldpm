import React, { useState } from 'react';
import { Calendar, Loader2 } from 'lucide-react';
import { Modal } from './Modal';
import { useCreateSchedule, useDisplays, useGroups } from '../hooks/useApi';

interface CreateScheduleModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CreateScheduleModal: React.FC<CreateScheduleModalProps> = ({ isOpen, onClose }) => {
  const createMutation = useCreateSchedule();
  const { data: displays } = useDisplays();
  const { data: groups } = useGroups();
  
  const [formData, setFormData] = useState({
    name: '',
    cron_expression: '',
    action: 'on' as 'on' | 'off',
    targetType: 'display' as 'display' | 'group',
    display_id: '',
    group_id: '',
    enabled: true,
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Schedule name is required';
    }

    if (!formData.cron_expression.trim()) {
      newErrors.cron_expression = 'Cron expression is required';
    } else {
      const parts = formData.cron_expression.trim().split(/\s+/);
      if (parts.length !== 5) {
        newErrors.cron_expression = 'Cron expression must have 5 fields (minute hour day month day_of_week)';
      }
    }

    if (formData.targetType === 'display' && !formData.display_id) {
      newErrors.display_id = 'Please select a display';
    }

    if (formData.targetType === 'group' && !formData.group_id) {
      newErrors.group_id = 'Please select a group';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validate()) return;

    const payload: any = {
      name: formData.name.trim(),
      cron_expression: formData.cron_expression.trim(),
      action: formData.action,
      enabled: formData.enabled,
    };

    if (formData.targetType === 'display') {
      payload.display_id = parseInt(formData.display_id);
    } else {
      payload.group_id = parseInt(formData.group_id);
    }

    createMutation.mutate(payload, {
      onSuccess: () => {
        setFormData({
          name: '',
          cron_expression: '',
          action: 'on',
          targetType: 'display',
          display_id: '',
          group_id: '',
          enabled: true,
        });
        setErrors({});
        onClose();
      },
    });
  };

  const handleClose = () => {
    setFormData({
      name: '',
      cron_expression: '',
      action: 'on',
      targetType: 'display',
      display_id: '',
      group_id: '',
      enabled: true,
    });
    setErrors({});
    createMutation.reset();
    onClose();
  };

  const cronExamples = [
    { label: '8:00 AM Weekdays', value: '0 8 * * 1-5' },
    { label: '6:00 PM Daily', value: '0 18 * * *' },
    { label: '12:30 PM Sundays', value: '30 12 * * 0' },
  ];

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Create Schedule">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Name */}
        <div>
          <label htmlFor="schedule-name" className="block text-sm font-medium text-slate-300 mb-1">
            Schedule Name <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            id="schedule-name"
            value={formData.name}
            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Morning Startup"
          />
          {errors.name && <p className="mt-1 text-sm text-red-400">{errors.name}</p>}
        </div>

        {/* Cron Expression */}
        <div>
          <label htmlFor="cron" className="block text-sm font-medium text-slate-300 mb-1">
            Cron Expression <span className="text-red-400">*</span>
          </label>
          <input
            type="text"
            id="cron"
            value={formData.cron_expression}
            onChange={(e) => setFormData({ ...formData, cron_expression: e.target.value })}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
            placeholder="0 8 * * 1-5"
          />
          {errors.cron_expression && <p className="mt-1 text-sm text-red-400">{errors.cron_expression}</p>}
          <p className="mt-1 text-xs text-slate-400">Format: minute hour day month day_of_week</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {cronExamples.map((example) => (
              <button
                key={example.value}
                type="button"
                onClick={() => setFormData({ ...formData, cron_expression: example.value })}
                className="text-xs px-2 py-1 bg-slate-700/50 text-slate-300 rounded hover:bg-slate-700 transition-colors"
              >
                {example.label}
              </button>
            ))}
          </div>
        </div>

        {/* Action */}
        <div>
          <label htmlFor="action" className="block text-sm font-medium text-slate-300 mb-1">
            Action <span className="text-red-400">*</span>
          </label>
          <select
            id="action"
            value={formData.action}
            onChange={(e) => setFormData({ ...formData, action: e.target.value as 'on' | 'off' })}
            className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="on">Power On</option>
            <option value="off">Power Off</option>
          </select>
        </div>

        {/* Target Type */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Target <span className="text-red-400">*</span>
          </label>
          <div className="flex space-x-4">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="radio"
                value="display"
                checked={formData.targetType === 'display'}
                onChange={(e) => setFormData({ ...formData, targetType: e.target.value as 'display', display_id: '', group_id: '' })}
                className="w-4 h-4 text-blue-600 bg-slate-900 border-slate-700 focus:ring-blue-500"
              />
              <span className="text-slate-300">Display</span>
            </label>
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="radio"
                value="group"
                checked={formData.targetType === 'group'}
                onChange={(e) => setFormData({ ...formData, targetType: e.target.value as 'group', display_id: '', group_id: '' })}
                className="w-4 h-4 text-blue-600 bg-slate-900 border-slate-700 focus:ring-blue-500"
              />
              <span className="text-slate-300">Group</span>
            </label>
          </div>
        </div>

        {/* Display/Group Selector */}
        {formData.targetType === 'display' && (
          <div>
            <label htmlFor="display_id" className="block text-sm font-medium text-slate-300 mb-1">
              Select Display <span className="text-red-400">*</span>
            </label>
            <select
              id="display_id"
              value={formData.display_id}
              onChange={(e) => setFormData({ ...formData, display_id: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">-- Select a display --</option>
              {displays?.map((display) => (
                <option key={display.id} value={display.id}>
                  {display.name} ({display.ip_address})
                </option>
              ))}
            </select>
            {errors.display_id && <p className="mt-1 text-sm text-red-400">{errors.display_id}</p>}
          </div>
        )}

        {formData.targetType === 'group' && (
          <div>
            <label htmlFor="group_id" className="block text-sm font-medium text-slate-300 mb-1">
              Select Group <span className="text-red-400">*</span>
            </label>
            <select
              id="group_id"
              value={formData.group_id}
              onChange={(e) => setFormData({ ...formData, group_id: e.target.value })}
              className="w-full px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">-- Select a group --</option>
              {groups?.map((group) => (
                <option key={group.id} value={group.id}>
                  {group.name}
                </option>
              ))}
            </select>
            {errors.group_id && <p className="mt-1 text-sm text-red-400">{errors.group_id}</p>}
          </div>
        )}

        {/* Enabled Checkbox */}
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="enabled"
            checked={formData.enabled}
            onChange={(e) => setFormData({ ...formData, enabled: e.target.checked })}
            className="w-4 h-4 text-blue-600 bg-slate-900 border-slate-700 rounded focus:ring-blue-500"
          />
          <label htmlFor="enabled" className="text-sm text-slate-300 cursor-pointer">
            Enable immediately
          </label>
        </div>

        {/* Error Message */}
        {createMutation.isError && (
          <div className="p-3 bg-red-900/20 border border-red-500/50 rounded-lg">
            <p className="text-sm text-red-400">
              Failed to create schedule. Please try again.
            </p>
          </div>
        )}

        {/* Buttons */}
        <div className="flex space-x-3 pt-4">
          <button
            type="button"
            onClick={handleClose}
            disabled={createMutation.isPending}
            className="flex-1 px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
          >
            {createMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Creating...</span>
              </>
            ) : (
              <>
                <Calendar className="w-4 h-4" />
                <span>Create Schedule</span>
              </>
            )}
          </button>
        </div>
      </form>
    </Modal>
  );
};
