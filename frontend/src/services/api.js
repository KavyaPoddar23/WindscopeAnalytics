const API_BASE = import.meta.env.VITE_API_URL || "";

export async function fetchAnalysis(startDate, endDate) {
  const params = new URLSearchParams({
    start_date: startDate,
    end_date: endDate,
  });

  const response = await fetch(
    `${API_BASE}/api/analysis?${params.toString()}`
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));

    throw new Error(
      error.detail || "Unable to load analysis data"
    );
  }

  return response.json();
}