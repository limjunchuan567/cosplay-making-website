function getProjects() {
    return JSON.parse(localStorage.getItem('projects') || '[]');
}

function saveProjects(projects) {
    localStorage.setItem('projects', JSON.stringify(projects));
}

function renderProjects() {
    const list = document.getElementById('projectList');
    if (!list) {
        return;
    }

    const user = getCurrentUser();
    const projects = getProjects().filter((project) => project.userId === user.id);
    const emptyProjects = document.getElementById('emptyProjects');
    emptyProjects.hidden = projects.length > 0;
    list.replaceChildren();

    for (const project of projects) {
        const item = document.createElement('li');
        item.className = 'card';
        const link = document.createElement('a');
        link.href = `project-view.html?id=${encodeURIComponent(project.id)}`;
        link.textContent = project.name;
        item.append(link);
        list.append(item);
    }
}

const projectForm = document.getElementById('projectForm');
if (projectForm) {
    const currentUser = requireAuth();
    const projectId = new URLSearchParams(window.location.search).get('id');
    const existingProject = currentUser && projectId
        ? getProjects().find(
            (project) => project.id === projectId && project.userId === currentUser.id
        )
        : null;
    const isProjectView = projectForm.dataset.projectView === 'true';

    if (!currentUser) {
        projectForm.hidden = true;
    } else if (isProjectView && (!projectId || !existingProject)) {
        window.location.replace('dashboard.html');
    } else if (existingProject) {
        document.getElementById('projectName').value = existingProject.name;
        document.getElementById('projectCharacter').value = existingProject.character || '';
        document.getElementById('projectNotes').value = existingProject.notes || '';
        document.getElementById('deleteProject').hidden = false;
    }

    projectForm.addEventListener('submit', (event) => {
        event.preventDefault();
        if (!currentUser) {
            return;
        }

        const projects = getProjects();
        const project = {
            id: existingProject ? existingProject.id : String(Date.now()),
            userId: currentUser.id,
            name: document.getElementById('projectName').value.trim(),
            character: document.getElementById('projectCharacter').value.trim(),
            notes: document.getElementById('projectNotes').value.trim(),
            updatedAt: new Date().toISOString()
        };
        const projectIndex = projects.findIndex((item) => item.id === project.id);

        if (projectIndex === -1) {
            projects.push(project);
        } else {
            projects[projectIndex] = project;
        }
        saveProjects(projects);
        window.location.href = `project-view.html?id=${encodeURIComponent(project.id)}`;
    });

    const deleteButton = document.getElementById('deleteProject');
    if (deleteButton) {
        deleteButton.addEventListener('click', () => {
            if (!existingProject) {
                return;
            }
            saveProjects(getProjects().filter((project) => project.id !== existingProject.id));
            window.location.href = 'dashboard.html';
        });
    }
}
