import axios, { type AxiosInstance, type AxiosError, type AxiosRequestConfig } from 'axios';
import type { ApiResponse, ApiError } from '@/types';
import { authHelpers } from '@/lib/supabase';

/**
 * API Configuration (Next.js)
 */
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:5001/api';
const API_TIMEOUT = parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT || '30000', 10);

/**
 * Create Axios instance with default configuration
 */
export const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: API_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request interceptor for adding auth token
 */
apiClient.interceptors.request.use(
  async (config) => {
    // Only add auth headers in browser context
    if (typeof window !== 'undefined') {
      try {
        // Get current Supabase session
        const { session, error } = await authHelpers.getSession();

        if (error) {
          console.error('Session error:', error);
        }

        if (!error && session) {
          // Add JWT token to Authorization header
          config.headers.Authorization = `Bearer ${session.access_token}`;

          // Add user ID to X-User-ID header
          if (session.user?.id) {
            config.headers['X-User-ID'] = session.user.id;
          }

          console.log('API Request with auth:', {
            url: config.url,
            method: config.method,
            hasAuth: !!session.access_token,
            userId: session.user?.id
          });
        } else {
          console.warn('No session found for API request to:', config.url);
        }
      } catch (error) {
        console.error('Failed to get session for API request:', error);
      }
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor for handling errors
 */
apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError<ApiError>) => {
    console.error('API Error:', error);

    // Handle specific error cases
    if (error.response) {
      const { status, data } = error.response;

      switch (status) {
        case 401:
          // TODO: Handle unauthorized - redirect to login or refresh token
          console.error('Unauthorized - session may have expired');
          break;
        case 403:
          console.error('Forbidden - insufficient permissions');
          break;
        case 404:
          console.error('Resource not found');
          break;
        case 429:
          console.error('Rate limited - too many requests');
          break;
        case 500:
          console.error('Server error');
          break;
      }

      // Return a standardized error
      const apiError: ApiError = {
        code: data?.code || `HTTP_${status}`,
        message: data?.message || data?.error || error.message || 'An error occurred',
        details: data?.details,
      };

      return Promise.reject(apiError);
    }

    // Network errors
    if (error.request) {
      console.error('Network error - unable to reach server');
      const networkError: ApiError = {
        code: 'NETWORK_ERROR',
        message: 'Unable to connect to the server. Please check your connection and ensure the backend is running.',
      };
      return Promise.reject(networkError);
    }

    // Other errors (e.g., request setup errors)
    const genericError: ApiError = {
      code: 'UNKNOWN_ERROR',
      message: error.message || 'An unexpected error occurred',
    };
    return Promise.reject(genericError);
  }
);

/**
 * Generic API request helper
 */
export async function apiRequest<T>(config: AxiosRequestConfig): Promise<T> {
  const response = await apiClient.request<ApiResponse<T>>(config);
  return response.data.data;
}

/**
 * GET request helper
 */
export async function get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return apiRequest<T>({ ...config, method: 'GET', url });
}

/**
 * POST request helper
 */
export async function post<T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  return apiRequest<T>({ ...config, method: 'POST', url, data });
}

/**
 * PUT request helper
 */
export async function put<T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  return apiRequest<T>({ ...config, method: 'PUT', url, data });
}

/**
 * PATCH request helper
 */
export async function patch<T>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
): Promise<T> {
  return apiRequest<T>({ ...config, method: 'PATCH', url, data });
}

/**
 * DELETE request helper
 */
export async function del<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
  return apiRequest<T>({ ...config, method: 'DELETE', url });
}

export default apiClient;
