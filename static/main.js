function filterTeams() {
    const input = document.getElementById("teamSearch");
    const filter = input.value.toUpperCase();
    localStorage.setItem('teamSearch', input.value); // Save the search term to localStorage
    const stages = document.querySelectorAll(".stage");

    stages.forEach(stage => {
        const teamRows = stage.querySelectorAll(".team-row");
        let allHidden = true;

        teamRows.forEach(row => {
            const txtValue = row.getAttribute("data-tags");
            if (txtValue && txtValue.toUpperCase().indexOf(filter) > -1) {
                row.style.display = "";
                allHidden = false;
            } else {
                row.style.display = "none";
            }
        });

        if (allHidden) {
            stage.style.display = "none";
        } else {
            stage.style.display = "";
        }
    });
}
function clearSearchInput() {
    const input = document.getElementById("teamSearch");
    input.value = "";
    localStorage.removeItem('teamSearch');
    filterTeams();
    input.focus()
}

const groupTableModal = document.getElementById('groupTableModal');
const groupTableModalTitle = document.getElementById('groupTableModalTitle');
const groupTableModalBody = document.getElementById('groupTableModalBody');
const groupTableModalStatus = document.getElementById('groupTableModalStatus');

function setGroupTableStatus(message) {
    groupTableModalStatus.textContent = message;
    groupTableModalStatus.hidden = !message;
}

function renderGroupTableRows(scores) {
    groupTableModalBody.innerHTML = '';

    scores.forEach((score) => {
        const row = document.createElement('tr');
        [
            score.position,
            score.team.name,
            score.group_points,
            score.difference_in_points,
            score.scored_points,
        ].forEach((value) => {
            const cell = document.createElement('td');
            cell.textContent = value;
            row.appendChild(cell);
        });
        groupTableModalBody.appendChild(row);
    });
}

function openGroupTableModal(button) {
    const groupId = button.dataset.groupId;
    const groupName = button.dataset.groupName;

    groupTableModalTitle.textContent = `${groupName} Tabelle`;
    groupTableModal.hidden = false;
    document.body.classList.add('modal-open');
    groupTableModalBody.innerHTML = '';
    setGroupTableStatus('Lade Tabelle...');

    fetch(`/groups/${groupId}/table`)
        .then((response) => {
            if (!response.ok) {
                throw new Error('Failed to load group table');
            }
            return response.json();
        })
        .then((group) => {
            renderGroupTableRows(group.scores);
            setGroupTableStatus(group.scores.length ? '' : 'Keine Tabellenwerte verfügbar.');
        })
        .catch(() => {
            setGroupTableStatus('Die Tabelle konnte nicht geladen werden.');
        });
}

function closeGroupTableModal() {
    groupTableModal.hidden = true;
    document.body.classList.remove('modal-open');
}

// Focus search input on page load and restore the search term
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('teamSearch');
    const savedSearch = localStorage.getItem('teamSearch');
    if (savedSearch) {
        searchInput.value = savedSearch;
        filterTeams(); // Apply the filter with the saved search term
    }
    searchInput.focus();
});

// Shortcut to focus search input with cmd/ctrl + k
document.addEventListener('keydown', function(event) {
    if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        document.getElementById('teamSearch').focus();
    }

    if (event.key === 'Escape' && groupTableModal && !groupTableModal.hidden) {
        closeGroupTableModal();
    }
});
