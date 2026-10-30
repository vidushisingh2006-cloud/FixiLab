export function getApiUrl(path: string) {
  const configuredUrl = import.meta.env.VITE_API_URL;
  
  let baseUrl = configuredUrl;
  if (!baseUrl) {
    if (typeof window !== "undefined") {
      // On the client, use the current hostname
      baseUrl = `http://${window.location.hostname}:8000`;
    } else {
      // On the server (SSR), default to localhost
      baseUrl = "http://localhost:8000";
    }
  }

  return `${baseUrl.replace(/\/+$/, "")}/${path.replace(/^\/+/, "")}`;
}

export async function getApiError(response: Response) {
  try {
    const body: unknown = await response.json();
    if (
      typeof body === "object" &&
      body !== null &&
      "detail" in body &&
      typeof body.detail === "string"
    ) {
      return body.detail;
    }
  } catch {
    // Use the HTTP status when the server does not return a JSON error.
  }

  return `Request failed (${response.status})`;
}
