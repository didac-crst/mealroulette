const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type HealthResponse = {
  status: string;
};

export async function fetchHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/api/health`);

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}
