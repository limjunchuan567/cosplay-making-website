function getDashboardProjects() {
    return JSON.parse(localStorage.getItem('projects') || '[]');
}

function renderProjects() {
    const emptyState = document.getElementById('emptyState');
    const projectsGrid = document.getElementById('projectsGrid');
    const viewAllButton = document.getElementById('viewAllBtn');
    const projects = getDashboardProjects();

    emptyState.hidden = projects.length > 0;
    projectsGrid.hidden = projects.length === 0;
    viewAllButton.hidden = projects.length === 0;
    projectsGrid.replaceChildren();

    for (const project of projects) {
        const card = document.createElement('article');
        card.className = 'card project-card';

        const title = document.createElement('h3');
        title.className = 'card-title';
        title.textContent = project.characterName || project.name || 'Untitled project';

        const subtitle = document.createElement('p');
        subtitle.className = 'card-subtitle';
        subtitle.textContent = project.source || project.character || 'Cosplay project';

        const details = document.createElement('p');
        details.className = 'project-meta';
        const conventionDate = project.conventionDate ? new Date(project.conventionDate) : null;
        details.textContent = conventionDate && !Number.isNaN(conventionDate.getTime())
            ? `Convention: ${conventionDate.toLocaleDateString()}`
            : 'Convention date not set';

        const link = document.createElement('a');
        link.className = 'btn btn-primary btn-small';
        link.href = `project-view.html?id=${encodeURIComponent(project.id)}`;
        link.textContent = 'Open Project';

        card.append(title, subtitle, details, link);
        projectsGrid.append(card);
    }
}

const logoutButton = document.getElementById('logoutButton');
if (logoutButton) {
    logoutButton.addEventListener('click', () => {
        localStorage.removeItem('currentUser');
        window.location.href = '../index.html';
    });
}

if (!localStorage.getItem('currentUser')) {
    window.location.replace('../index.html');
} else {
    document.addEventListener('DOMContentLoaded', renderProjects);
}
