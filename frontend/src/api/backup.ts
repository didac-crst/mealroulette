import { apiRequest } from "./client";

export type BackupSettings = {
  enabled: boolean;
  run_time: string;
  timezone: string;
  retention_days: number;
  backup_path: string;
  include_json_export: boolean;
  include_pg_dump: boolean;
  last_backup_at: string | null;
  last_error: string | null;
};

export type BackupSettingsInput = Partial<
  Pick<
    BackupSettings,
    | "enabled"
    | "run_time"
    | "timezone"
    | "retention_days"
    | "backup_path"
    | "include_json_export"
    | "include_pg_dump"
  >
>;

export type BackupRun = {
  id: number;
  backup_type: string;
  status: string;
  file_path: string | null;
  file_size_bytes: number | null;
  checksum_sha256: string | null;
  started_at: string;
  finished_at: string | null;
  error_message: string | null;
  created_at: string;
};

function withToken(token: string) {
  return { token };
}

export async function fetchBackupSettings(token: string): Promise<BackupSettings> {
  return apiRequest<BackupSettings>("/api/backups/settings", withToken(token));
}

export async function updateBackupSettings(
  token: string,
  payload: BackupSettingsInput,
): Promise<BackupSettings> {
  return apiRequest<BackupSettings>("/api/backups/settings", {
    method: "PUT",
    body: JSON.stringify(payload),
    ...withToken(token),
  });
}

export async function fetchBackupRuns(token: string): Promise<BackupRun[]> {
  return apiRequest<BackupRun[]>("/api/backups", withToken(token));
}

export async function runBackupNow(token: string): Promise<BackupRun[]> {
  return apiRequest<BackupRun[]>("/api/backups/run", {
    method: "POST",
    ...withToken(token),
  });
}
