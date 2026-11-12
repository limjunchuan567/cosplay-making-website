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
    // Auth disabled for now — returns a default guest user
    return { id: 'guest', name: 'Cosplayer' };
}

function requireAuth() {
    // Auth disabled for now — always returns guest user
    return getCurrentUser();
}
