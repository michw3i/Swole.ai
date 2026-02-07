// API Configuration
export const API_BASE_URL = 'http://localhost:8000';

export const API_ENDPOINTS = {
  createUser: '/api/users',
  getUser: (userId) => `/api/users/${userId}`,
  getWorkoutTypes: '/api/workout-types',
  generateWorkout: '/api/workouts/generate',
  getWorkout: (workoutId) => `/api/workouts/${workoutId}`,
  submitFeedback: (workoutId) => `/api/workouts/${workoutId}/feedback`,
  getUserWorkouts: (userId) => `/api/users/${userId}/workouts`,
  health: '/api/health'
};

// API Helper Functions
export const api = {
  // Create a new user
  async createUser(userData) {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.createUser}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(userData)
    });
    if (!response.ok) throw new Error('Failed to create user');
    return await response.json();
  },

  // Get user by ID
  async getUser(userId) {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.getUser(userId)}`);
    if (!response.ok) throw new Error('Failed to get user');
    return await response.json();
  },

  // Get available workout types
  async getWorkoutTypes() {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.getWorkoutTypes}`);
    if (!response.ok) throw new Error('Failed to get workout types');
    return await response.json();
  },

  // Generate a new workout
  async generateWorkout(workoutData) {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.generateWorkout}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(workoutData)
    });
    if (!response.ok) throw new Error('Failed to generate workout');
    return await response.json();
  },

  // Get workout by ID
  async getWorkout(workoutId) {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.getWorkout(workoutId)}`);
    if (!response.ok) throw new Error('Failed to get workout');
    return await response.json();
  },

  // Submit workout feedback
  async submitFeedback(workoutId, feedbackData) {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.submitFeedback(workoutId)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(feedbackData)
    });
    if (!response.ok) throw new Error('Failed to submit feedback');
    return await response.json();
  },

  // Get user's workout history
  async getUserWorkouts(userId, limit = 10) {
    const response = await fetch(
      `${API_BASE_URL}${API_ENDPOINTS.getUserWorkouts(userId)}?limit=${limit}`
    );
    if (!response.ok) throw new Error('Failed to get user workouts');
    return await response.json();
  },

  // Health check
  async checkHealth() {
    const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.health}`);
    if (!response.ok) throw new Error('Health check failed');
    return await response.json();
  }
};