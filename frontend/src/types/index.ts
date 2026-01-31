export interface Display {
  id: number;
  name: string;
  ip_address: string;
  location: string;
  tags: Record<string, any>;
  status: 'active' | 'standby' | 'offline' | 'unknown';
  last_seen: string | null;
  created_at: string;
}

export interface Group {
  id: number;
  name: string;
  description: string;
  display_count: number;
  created_at: string;
}

export interface Schedule {
  id: number;
  name: string;
  cron_expression: string;
  action: 'on' | 'off';
  enabled: boolean;
  display_id: number | null;
  group_id: number | null;
  created_at: string;
}
