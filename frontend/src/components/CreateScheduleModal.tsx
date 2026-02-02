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
    hour: '08',
    minute: '00',
    action: 'on' as 'on' | 'off',
    targetType: 'display' as 'display' | 'group',
    display_id: '',
    group_id: '',
    enabled: true,
    weekdays: {
      monday: true,
      tuesday: true,
      wednesday: true,
      thursday: true,
      friday: true,
      saturday: false,
      sunday: false,
    },
  });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const buildCronExpression = (): string => {
    const selectedDays = Object.entries(formData.weekdays)
      .map(([, enabled], index) => enabled ? index : -1)
      .filter(day => day !== -1);

    const dayOfWeek = selectedDays.length === 0 ? '*' : selectedDays.join(',');
    return `${formData.minute} ${formData.hour} * * ${dayOfWeek}`;
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Schedule name is required';
    }

    const selectedDaysCount = Object.values(formData.weekdays).filter(Boolean).length;
    if (selectedDaysCount === 0) {
      newErrors.weekdays = 'Please select at least one day';
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
      cron_expression: buildCronExpression(),
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
          hour: '08',
          minute: '00',
          action: 'on',
          targetType: 'display',
          display_id: '',
          group_id: '',
          enabled: true,
          weekdays: {
            monday: true,
            tuesday: true,
            wednesday: true,
            thursday: true,
            friday: true,
            saturday: false,
            sunday: false,
          },
        });
        setErrors({});
        onClose();
      },
    });
  };

  const handleClose = () => {
    setFormData({
      name: '',
      hour: '08',
      minute: '00',
      action: 'on',
      targetType: 'display',
      display_id: '',
      group_id: '',
      enabled: true,
      weekdays: {
        monday: true,
        tuesday: true,
        wednesday: true,
        thursday: true,
        friday: true,
        saturday: false,
        sunday: false,
      },
    });
    setErrors({});
    createMutation.reset();
    onClose();
  };

  const weekdayLabels = [
    { key: 'monday', label: 'Mon' },
    { key: 'tuesday', label: 'Tue' },
    { key: 'wednesday', label: 'Wed' },
    { key: 'thursday', label: 'Thu' },
    { key: 'friday', label: 'Fri' },
    { key: 'saturday', label: 'Sat' },
    { key: 'sunday', label: 'Sun' },
  ];

  const toggleWeekday = (day: string) => {
    setFormData({
      ...formData,
      weekdays: {
        ...formData.weekdays,
        [day]: !formData.weekdays[day as keyof typeof formData.weekdays],
      },
    });
  };

  const selectWeekdays = () => {
    setFormData({
      ...formData,
      weekdays: {
        monday: true,
        tuesday: true,
        wednesday: true,
        thursday: true,
        friday: true,
        saturday: false,
        sunday: false,
      },
    });
  };

  const selectWeekend = () => {
    setFormData({
      ...formData,
      weekdays: {
        monday: false,
        tuesday: false,
        wednesday: false,
        thursday: false,
        friday: false,
        saturday: true,
        sunday: true,
      },
    });
  };

  const selectAllDays = () => {
    setFormData({
      ...formData,
      weekdays: {
        monday: true,
        tuesday: true,
        wednesday: true,
        thursday: true,
        friday: true,
        saturday: true,
        sunday: true,
      },
    });
  };

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

        {/* Time Picker */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-1">
            Time <span className="text-red-400">*</span>
          </label>
          <div className="flex space-x-2">
            <select
              value={formData.hour}
              onChange={(e) => setFormData({ ...formData, hour: e.target.value })}
              className="flex-1 px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {Array.from({ length: 24 }, (_, i) => {
                const hour = i.toString().padStart(2, '0');
                return (
                  <option key={hour} value={hour}>
                    {hour}
                  </option>
                );
              })}
            </select>
            <span className="text-slate-300 text-xl leading-9">:</span>
            <select
              value={formData.minute}
              onChange={(e) => setFormData({ ...formData, minute: e.target.value })}
              className="flex-1 px-3 py-2 bg-slate-900 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {Array.from({ length: 60 }, (_, i) => {
                const minute = i.toString().padStart(2, '0');
                return (
                  <option key={minute} value={minute}>
                    {minute}
                  </option>
                );
              })}
            </select>
          </div>
          <p className="mt-1 text-xs text-slate-400">
            Current selection: {formData.hour}:{formData.minute}
          </p>
        </div>

        {/* Weekday Selector */}
        <div>
          <label className="block text-sm font-medium text-slate-300 mb-2">
            Days <span className="text-red-400">*</span>
          </label>
          <div className="flex flex-wrap gap-2 mb-2">
            {weekdayLabels.map(({ key, label }) => (
              <button
                key={key}
                type="button"
                onClick={() => toggleWeekday(key)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  formData.weekdays[key as keyof typeof formData.weekdays]
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={selectWeekdays}
              className="text-xs px-2 py-1 bg-slate-700/50 text-slate-300 rounded hover:bg-slate-700 transition-colors"
            >
              Weekdays
            </button>
            <button
              type="button"
              onClick={selectWeekend}
              className="text-xs px-2 py-1 bg-slate-700/50 text-slate-300 rounded hover:bg-slate-700 transition-colors"
            >
              Weekend
            </button>
            <button
              type="button"
              onClick={selectAllDays}
              className="text-xs px-2 py-1 bg-slate-700/50 text-slate-300 rounded hover:bg-slate-700 transition-colors"
            >
              Every Day
            </button>
          </div>
          {errors.weekdays && <p className="mt-2 text-sm text-red-400">{errors.weekdays}</p>}
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
