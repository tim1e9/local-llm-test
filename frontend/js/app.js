// API Configuration
const API_BASE = '/api';

// Authentication
let authToken = localStorage.getItem('auth_token');
let currentUser = null;

// DOM Elements
const loginView = document.getElementById('login-view');
const dashboardView = document.getElementById('dashboard-view');
const loginForm = document.getElementById('login-form');
const logoutBtn = document.getElementById('logout-btn');
const userName = document.getElementById('user-name');
const toastContainer = document.getElementById('toast-container');

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    checkAuthentication();
    setupEventListeners();
});

// Check if user is authenticated
async function checkAuthentication() {
    if (!authToken) {
        showView('login');
        return;
    }

    try {
        const user = await fetchUserProfile();
        if (user) {
            currentUser = user;
            showView('dashboard');
            updateUI();
            loadMyRequests();
            loadBalance();
        } else {
            logout();
        }
    } catch (error) {
        console.error('Authentication error:', error);
        logout();
    }
}

// Setup Event Listeners
function setupEventListeners() {
    // Login/Logout
    if (loginForm) loginForm.addEventListener('submit', handleLogin);
    if (logoutBtn) logoutBtn.addEventListener('click', logout);

    // Tab Navigation
    document.querySelectorAll('.btn-tab').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    // Vacation Form
    const vacationForm = document.getElementById('vacation-form');
    if (vacationForm) {
        vacationForm.addEventListener('submit', handleVacationRequest);
        
        // Calculate hours on date change
        const startDate = document.getElementById('start-date');
        const endDate = document.getElementById('end-date');
        if (startDate && endDate) {
            startDate.addEventListener('change', calculateHours);
            endDate.addEventListener('change', calculateHours);
        }
    }
}

// API Calls
async function fetchUserProfile() {
    const response = await fetch(`${API_BASE}/user/profile`, {
        headers: getAuthHeaders()
    });
    if (!response.ok) throw new Error('Failed to fetch profile');
    return await response.json();
}

function getAuthHeaders() {
    return {
        'Authorization': `Bearer ${authToken}`,
        'Content-Type': 'application/json'
    };
}

// Authentication Functions
async function handleLogin(event) {
    event.preventDefault();
    const username = document.getElementById('username').value.trim();
    
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Login failed');
        }
        
        const data = await response.json();
        authToken = data.token;
        localStorage.setItem('auth_token', authToken);
        
        // Load user profile and show dashboard
        const user = await fetchUserProfile();
        if (user) {
            currentUser = user;
            showView('dashboard');
            updateUI();
            loadMyRequests();
            loadBalance();
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function login() {
    window.location.href = '/login';
}

function logout() {
    authToken = null;
    currentUser = null;
    localStorage.removeItem('auth_token');
    showView('login');
}

// View Management
function showView(viewName) {
    if (viewName === 'login') {
        loginView.classList.remove('hidden');
        dashboardView.classList.add('hidden');
    } else {
        loginView.classList.add('hidden');
        dashboardView.classList.remove('hidden');
    }
}

// UI Updates
function updateUI() {
    if (!currentUser) return;
    
    userName.textContent = currentUser.full_name || currentUser.username;
    
    // Show manager tab if user has MANAGER role
    const roles = currentUser.roles || [];
    if (roles.includes('MANAGER')) {
        document.querySelectorAll('.manager-only').forEach(el => {
            el.classList.remove('hidden');
        });
    }
}

// Tab Switching
function switchTab(tabName) {
    // Update active tab button
    document.querySelectorAll('.btn-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tabName);
    });
    
    // Show/hide tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('hidden', content.id !== tabName);
    });
    
    // Load data for specific tabs
    if (tabName === 'pending-approvals') {
        loadPendingApprovals();
    }
}

// Vacation Requests
async function loadMyRequests() {
    try {
        const response = await fetch(`${API_BASE}/vacation/requests`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch requests');
        
        const requests = await response.json();
        displayRequests(requests, 'requests-list');
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function displayRequests(requests, containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    if (requests.length === 0) {
        container.innerHTML = '<p class="empty-message">No requests found</p>';
        return;
    }
    
    container.innerHTML = requests.map(req => `
        <div class="card">
            <h3>${formatDate(req.start_date)} - ${formatDate(req.end_date)}</h3>
            <p>Hours: ${req.hours_requested}</p>
            <p>Type: ${req.request_type.replace(/_/g, ' ')}</p>
            ${req.reason ? `<p>Reason: ${req.reason}</p>` : ''}
            <span class="status status-${req.status.toLowerCase()}">${req.status}</span>
        </div>
    `).join('');
}

async function handleVacationRequest(event) {
    event.preventDefault();
    
    const data = {
        start_date: document.getElementById('start-date').value,
        end_date: document.getElementById('end-date').value,
        request_type: document.getElementById('request-type').value,
        reason: document.getElementById('reason').value
    };
    
    try {
        const response = await fetch(`${API_BASE}/vacation/requests`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to create request');
        }
        
        showToast('Vacation request submitted successfully!', 'success');
        event.target.reset();
        document.getElementById('hours-calculation').textContent = '0';
        switchTab('my-requests');
        loadMyRequests();
        loadBalance();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function calculateHours() {
    const startDate = document.getElementById('start-date').value;
    const endDate = document.getElementById('end-date').value;
    
    if (startDate && endDate) {
        const start = new Date(startDate);
        const end = new Date(endDate);
        const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
        document.getElementById('hours-calculation').textContent = days * 8;
    }
}

// Balance
async function loadBalance() {
    try {
        const response = await fetch(`${API_BASE}/vacation/balance`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch balance');
        
        const balance = await response.json();
        const container = document.getElementById('balance-info');

        if (balance && Object.keys(balance).length > 0) {
            const available = balance.balance_hours - balance.used_hours;
            container.innerHTML = `
                <p><strong>Year:</strong> ${balance.year}</p>
                <p><strong>Total Balance:</strong> ${balance.balance_hours} hours</p>
                <p><strong>Used:</strong> ${balance.used_hours} hours</p>
                <p><strong>Available:</strong> ${available} hours</p>
            `;
        } else {
            container.innerHTML = '<p>No balance information available</p>';
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Manager Approvals
async function loadPendingApprovals() {
    try {
        const response = await fetch(`${API_BASE}/vacation/pending`, {
            headers: getAuthHeaders()
        });
        if (!response.ok) throw new Error('Failed to fetch pending requests');
        
        const requests = await response.json();
        displayPendingRequests(requests);
    } catch (error) {
        showToast(error.message, 'error');
    }
}

function displayPendingRequests(requests) {
    const container = document.getElementById('pending-list');
    if (!container) return;
    
    if (requests.length === 0) {
        container.innerHTML = '<p class="empty-message">No pending approvals</p>';
        return;
    }
    
    container.innerHTML = requests.map(req => `
        <div class="card">
            <h3>${formatDate(req.start_date)} - ${formatDate(req.end_date)}</h3>
            <p>Hours: ${req.hours_requested}</p>
            <p>Type: ${req.request_type.replace(/_/g, ' ')}</p>
            ${req.reason ? `<p>Reason: ${req.reason}</p>` : ''}
            <div class="card-actions">
                <button class="btn btn-approve" onclick="approveRequest(${req.id})">Approve</button>
                <button class="btn btn-reject" onclick="rejectRequest(${req.id})">Reject</button>
            </div>
        </div>
    `).join('');
}

async function approveRequest(requestId) {
    try {
        const response = await fetch(`${API_BASE}/vacation/approve/${requestId}`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        
        if (!response.ok) throw new Error('Failed to approve request');
        
        showToast('Request approved successfully!', 'success');
        loadPendingApprovals();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

async function rejectRequest(requestId) {
    try {
        const response = await fetch(`${API_BASE}/vacation/reject/${requestId}`, {
            method: 'POST',
            headers: getAuthHeaders()
        });
        
        if (!response.ok) throw new Error('Failed to reject request');
        
        showToast('Request rejected', 'success');
        loadPendingApprovals();
    } catch (error) {
        showToast(error.message, 'error');
    }
}

// Toast Notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// Utilities
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}
