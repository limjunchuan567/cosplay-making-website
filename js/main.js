function getUsers() {
    return JSON.parse(localStorage.getItem('users') || '[]');
}

function saveUsers(users) {
    localStorage.setItem('users', JSON.stringify(users));
}

function showMessage(elementId, message, type) {
    const messageElement = document.getElementById(elementId);
    if (!messageElement) {
        return;
    }

    messageElement.textContent = message;
    messageElement.className = `message ${type}`;
    window.setTimeout(() => {
        messageElement.className = 'message';
    }, 3000);
}

function getCurrentUser() {
    return JSON.parse(localStorage.getItem('currentUser') || 'null');
}

function requireAuth() {
    const user = getCurrentUser();
    if (!user) {
        window.location.replace('../index.html');
        return null;
    }
    return user;
}

function logout() {
    localStorage.removeItem('currentUser');
    window.location.href = '../index.html';
}
