import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../api/client';
import { Display, Group, Schedule } from '../types';

// ============================================
// DISPLAY HOOKS
// ============================================

export const useDisplays = () => {
  return useQuery({
    queryKey: ['displays'],
    queryFn: async () => {
      const { data } = await apiClient.get<Display[]>('/displays');
      return data;
    },
    refetchInterval: 30000, // Auto-refresh every 30 seconds
  });
};

export const useDisplay = (id: number) => {
  return useQuery({
    queryKey: ['displays', id],
    queryFn: async () => {
      const { data } = await apiClient.get<Display>(`/displays/${id}`);
      return data;
    },
    enabled: !!id,
  });
};

export const useCreateDisplay = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (display: Omit<Display, 'id' | 'created_at' | 'last_seen'>) => {
      const { data } = await apiClient.post<Display>('/displays', display);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['displays'] });
    },
  });
};

export const useUpdateDisplay = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...display }: Partial<Display> & { id: number }) => {
      const { data } = await apiClient.put<Display>(`/displays/${id}`, display);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['displays'] });
    },
  });
};

export const useDeleteDisplay = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/displays/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['displays'] });
    },
  });
};

export const usePowerControl = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, state }: { id: number; state: 'on' | 'off' }) => {
      const { data } = await apiClient.post(`/displays/${id}/power`, { on: state === 'on' });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['displays'] });
    },
  });
};

export const useImportCSV = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      const { data } = await apiClient.post('/displays/import', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['displays'] });
    },
  });
};

// ============================================
// GROUP HOOKS
// ============================================

export const useGroups = () => {
  return useQuery({
    queryKey: ['groups'],
    queryFn: async () => {
      const { data } = await apiClient.get<Group[]>('/groups');
      return data;
    },
  });
};

export const useGroup = (id: number) => {
  return useQuery({
    queryKey: ['groups', id],
    queryFn: async () => {
      const { data } = await apiClient.get<Group>(`/groups/${id}`);
      return data;
    },
    enabled: !!id,
  });
};

export const useCreateGroup = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (group: Omit<Group, 'id' | 'created_at' | 'display_count'>) => {
      const { data } = await apiClient.post<Group>('/groups', group);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] });
    },
  });
};

export const useUpdateGroup = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...group }: Partial<Group> & { id: number }) => {
      const { data } = await apiClient.put<Group>(`/groups/${id}`, group);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] });
    },
  });
};

export const useDeleteGroup = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/groups/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['groups'] });
    },
  });
};

export const useGroupPowerControl = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, state }: { id: number; state: 'on' | 'off' }) => {
      const { data } = await apiClient.post(`/groups/${id}/power`, { on: state === 'on' });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['displays'] });
      queryClient.invalidateQueries({ queryKey: ['groups'] });
    },
  });
};

// ============================================
// SCHEDULE HOOKS
// ============================================

export const useSchedules = () => {
  return useQuery({
    queryKey: ['schedules'],
    queryFn: async () => {
      const { data } = await apiClient.get<Schedule[]>('/schedules');
      return data;
    },
  });
};

export const useSchedule = (id: number) => {
  return useQuery({
    queryKey: ['schedules', id],
    queryFn: async () => {
      const { data } = await apiClient.get<Schedule>(`/schedules/${id}`);
      return data;
    },
    enabled: !!id,
  });
};

export const useCreateSchedule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (schedule: Omit<Schedule, 'id' | 'created_at'>) => {
      const { data } = await apiClient.post<Schedule>('/schedules', schedule);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
    },
  });
};

export const useUpdateSchedule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, ...schedule }: Partial<Schedule> & { id: number }) => {
      const { data } = await apiClient.put<Schedule>(`/schedules/${id}`, schedule);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
    },
  });
};

export const useDeleteSchedule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (id: number) => {
      await apiClient.delete(`/schedules/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
    },
  });
};

export const useToggleSchedule = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, enabled }: { id: number; enabled: boolean }) => {
      const endpoint = enabled ? 'enable' : 'disable';
      const { data } = await apiClient.post(`/schedules/${id}/${endpoint}`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['schedules'] });
    },
  });
};
