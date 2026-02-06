/**
 * API client for communicating with the backend.
 * To be implemented in Week 2.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = {
  baseUrl: API_URL,
  
  // TODO: Implement API methods
  // chat: {
  //   sendMessage: async (message: string) => {},
  //   streamMessage: async (message: string) => {},
  // },
  // documents: {
  //   upload: async (file: File) => {},
  //   list: async () => {},
  //   delete: async (id: string) => {},
  // },
};

export default apiClient;
