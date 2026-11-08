const currentUser = requireAuth();

if (currentUser) {
    document.getElementById('userName').textContent = currentUser.name;
    document.getElementById('userEmail').textContent = currentUser.email;
    document.getElementById('userDate').textContent =
        new Date(currentUser.createdAt).toLocaleDateString();
    document.getElementById('logoutButton').addEventListener('click', logout);
    renderProjects();
}
