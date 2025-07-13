import axios from 'axios'
import type { DashboardData } from '@/types/dashboard'

const api = axios.create({
  baseURL: '/api',
  timeout: 30000
})

export const dashboardService = {
  async getDashboardData(params?: {
    day?: string
    time?: string
    view_type?: string
  }): Promise<DashboardData> {
    const response = await api.get('', { params })
    return response.data
  },

  async regenerateOptimization(): Promise<void> {
    await api.post('/regenerate')
  },

  async downloadCSV(params?: {
    day?: string
    time?: string
  }): Promise<Blob> {
    const response = await api.get('/download_csv', {
      params,
      responseType: 'blob'
    })
    return response.data
  },

  async getSettings(): Promise<any> {
    const response = await api.get('/settings')
    return response.data
  },

  async updateSettings(settings: any): Promise<void> {
    await api.post('/settings', settings)
  }
}

export default api
