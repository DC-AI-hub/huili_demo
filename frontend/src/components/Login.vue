<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <div class="logo-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-columns">
            <path d="M12 3h7a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-7m0-18H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h7m0-18v18"></path>
          </svg>
        </div>
        <h1>Institutional<br/>Alpha</h1>
        <p class="subtitle">FUND MANAGEMENT</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="form-group">
          <label for="username">Username</label>
          <input 
            type="text" 
            id="username" 
            v-model="username" 
            placeholder="Enter your username" 
            required 
          />
        </div>
        
        <div class="form-group">
          <label for="password">Password</label>
          <input 
            type="password" 
            id="password" 
            v-model="password" 
            placeholder="Enter your password" 
            required 
          />
        </div>

        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>

        <button type="submit" class="login-btn">Sign In</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('anthony')
const password = ref('ay-123456')
const errorMessage = ref('')

const handleLogin = () => {
  if (username.value === 'anthony' && password.value === 'ay-123456') {
    localStorage.setItem('isAuthenticated', 'true')
    localStorage.setItem('currentUser', username.value)
    errorMessage.value = ''
    router.push('/lcreport')
  } else {
    errorMessage.value = 'Invalid username or password'
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f4f6f8;
  /* Cancel out padding from main-content in App.vue if applicable */
  margin: -2rem; 
  font-family: 'Inter', -apple-system, sans-serif;
}

.login-card {
  background: white;
  padding: 3rem 2.5rem;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-width: 380px;
}

.login-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.logo-icon {
  color: #1a252f;
  margin-bottom: 0.5rem;
  display: flex;
  justify-content: center;
}

.login-header h1 {
  font-size: 1.5rem;
  color: #1a252f;
  margin: 0;
  line-height: 1.2;
  font-weight: 700;
}

.subtitle {
  font-size: 0.7rem;
  color: #7f8c8d;
  letter-spacing: 2px;
  margin-top: 0.5rem;
  text-transform: uppercase;
  font-weight: 600;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #34495e;
}

.form-group input {
  padding: 0.75rem 1rem;
  border: 1px solid #e0e6ed;
  border-radius: 6px;
  font-size: 1rem;
  transition: all 0.2s;
  background-color: #f8f9fa;
}

.form-group input:focus {
  outline: none;
  border-color: #2e7d32;
  background-color: white;
  box-shadow: 0 0 0 3px rgba(46, 125, 50, 0.1);
}

.error-message {
  color: #e74c3c;
  font-size: 0.875rem;
  text-align: center;
  background: #fdf0ed;
  padding: 0.75rem;
  border-radius: 6px;
  font-weight: 500;
}

.login-btn {
  background-color: #388e3c;
  color: white;
  border: none;
  padding: 0.875rem;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, transform 0.1s;
  margin-top: 0.5rem;
}

.login-btn:hover {
  background-color: #2e7d32;
}

.login-btn:active {
  transform: translateY(1px);
}
</style>
