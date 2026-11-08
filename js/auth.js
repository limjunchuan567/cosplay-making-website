// ============================================
// AUTHENTICATION LOGIC
// ============================================

// Simple user storage using localStorage
const getUsers = () => {
    const users = localStorage.getItem('users');
    return users ? JSON.parse(users) : [];
};

const saveUsers = (users) => {
    localStorage.setItem('users', JSON.stringify(users));
};

// Show message function
const showMessage = (elementId, message, type) => {
    const messageEl = document.getElementById(elementId);
    if (!messageEl) return;
    
    messageEl.textContent = message;
    messageEl.className = `message ${type}`;
    
    setTimeout(() => {
        messageEl.className = 'message';
    }, 3000);
};

// Register form handler
const registerForm = document.getElementById('registerForm');
if (registerForm) {
    registerForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const name = document.getElementById('registerName').value.trim();
        const email = document.getElementById('registerEmail').value.trim();
        const password = document.getElementById('registerPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        // Validation
        if (password !== confirmPassword) {
            showMessage('registerMessage', 'Passwords do not match!', 'error');
            return;
        }
        
        if (password.length < 6) {
            showMessage('registerMessage', 'Password must be at least 6 characters!', 'error');
            return;
        }
        
        const users = getUsers();
        
        // Check if email already exists
        if (users.find(user => user.email === email)) {
            showMessage('registerMessage', 'Email already registered!', 'error');
            return;
        }
        
        // Create new user
        const newUser = {
            id: Date.now(),
            name,
            email,
            password,
            createdAt: new Date().toISOString()
        };
        
        users.push(newUser);
        saveUsers(users);
        
        showMessage('registerMessage', 'Registration successful! Redirecting to login...', 'success');
        
        setTimeout(() => {
            window.location.href = '../index.html';
        }, 1500);
    });
}

// Login form handler
const loginForm = document.getElementById('loginForm');
if (loginForm) {
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const email = document.getElementById('loginEmail').value.trim();
        const password = document.getElementById('loginPassword').value;
        
        const users = getUsers();
        const user = users.find(u => u.email === email && u.password === password);
        
        if (user) {
            // Store logged in user
            localStorage.setItem('currentUser', JSON.stringify(user));
            showMessage('loginMessage', 'Login successful! Welcome back, ' + user.name, 'success');
            
            setTimeout(() => {
                // Redirect to dashboard
                window.location.href = 'pages/dashboard.html';
            }, 1500);
        } else {
            showMessage('loginMessage', 'Invalid email or password!', 'error');
        }
    });
}