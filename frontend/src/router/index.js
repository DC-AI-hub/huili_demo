import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from '../components/Dashboard.vue'
import GenerateReport from '../components/GenerateReport.vue'
import ReportContainer from '../components/ReportContainer.vue'
import Login from '../components/Login.vue'
import LCReport from '../components/LCReport.vue'

const routes = [
    {
        path: '/login',
        name: 'Login',
        component: Login
    },
    {
        path: '/',
        name: 'Dashboard',
        component: Dashboard,
        meta: { requiresAuth: true }
    },
    {
        path: '/lcreport',
        name: 'LCReport',
        component: LCReport,
        meta: { requiresAuth: true }
    },
    {
        path: '/generate',
        name: 'Generate',
        component: GenerateReport,
        meta: { requiresAuth: true }
    },
    {
        path: '/report',
        name: 'Report',
        component: ReportContainer,
        meta: { requiresAuth: true }
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

router.beforeEach((to, from, next) => {
    const isAuthenticated = localStorage.getItem('isAuthenticated') === 'true'
    if (to.meta.requiresAuth && !isAuthenticated) {
        next('/login')
    } else if (to.path === '/login' && isAuthenticated) {
        next('/lcreport')
    } else {
        next()
    }
})

export default router
