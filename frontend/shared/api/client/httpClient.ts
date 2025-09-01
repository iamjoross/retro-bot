import { API_CONFIG } from "./config";

export class APIError extends Error {
  constructor(
    message: string,
    public status: number,
    public statusText: string,
    public url: string
  ) {
    super(message);
    this.name = "APIError";
  }
}

export interface RequestOptions extends RequestInit {
  timeout?: number;
  retries?: number;
}

class HTTPClient {
  private baseURL: string;

  constructor(baseURL: string = API_CONFIG.BASE_URL) {
    this.baseURL = baseURL;
  }

  private async executeRequest<T>(
    url: string,
    options: RequestOptions = {},
    attempt: number = 1
  ): Promise<T> {
    const {
      timeout = API_CONFIG.TIMEOUTS.DEFAULT,
      retries = API_CONFIG.RETRY.ATTEMPTS,
      ...fetchOptions
    } = options;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
      const response = await fetch(`${this.baseURL}${url}`, {
        ...fetchOptions,
        signal: controller.signal,
        headers: {
          "Content-Type": "application/json",
          ...fetchOptions.headers,
        },
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new APIError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status,
          response.statusText,
          url
        );
      }

      // Handle empty responses (204, etc.)
      if (
        response.status === 204 ||
        response.headers.get("content-length") === "0"
      ) {
        return {} as T;
      }

      const contentType = response.headers.get("content-type");
      if (contentType?.includes("application/json")) {
        return await response.json();
      }

      return (await response.text()) as unknown as T;
    } catch (error) {
      clearTimeout(timeoutId);

      // Handle abort/timeout
      if (error instanceof DOMException && error.name === "AbortError") {
        throw new APIError("Request timeout", 408, "Request Timeout", url);
      }

      // Retry logic for network errors and 5xx errors
      if (attempt < retries && this.shouldRetry(error)) {
        const delay = this.calculateRetryDelay(attempt);
        await this.sleep(delay);
        return this.executeRequest<T>(url, options, attempt + 1);
      }

      throw error;
    }
  }

  private shouldRetry(error: unknown): boolean {
    if (error instanceof APIError) {
      // Retry on server errors (5xx) but not client errors (4xx)
      return error.status >= 500;
    }

    // Retry on network errors
    return true;
  }

  private calculateRetryDelay(attempt: number): number {
    const baseDelay = API_CONFIG.RETRY.DELAY;
    return API_CONFIG.RETRY.EXPONENTIAL_BACKOFF
      ? baseDelay * Math.pow(2, attempt - 1)
      : baseDelay;
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async get<T>(url: string, options?: RequestOptions): Promise<T> {
    return this.executeRequest<T>(url, { ...options, method: "GET" });
  }

  async post<T>(
    url: string,
    data?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.executeRequest<T>(url, {
      ...options,
      method: "POST",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async patch<T>(
    url: string,
    data?: unknown,
    options?: RequestOptions
  ): Promise<T> {
    return this.executeRequest<T>(url, {
      ...options,
      method: "PATCH",
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  async delete<T>(url: string, options?: RequestOptions): Promise<T> {
    return this.executeRequest<T>(url, { ...options, method: "DELETE" });
  }
}

// Export singleton instance
export const httpClient = new HTTPClient();
