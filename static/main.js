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

function createCell(content) {
    const cell = document.createElement('td');
    if (content instanceof Node) {
        cell.appendChild(content);
    } else {
        cell.textContent = content;
    }
    return cell;
}

function deciderMatchById(group, matchId) {
    return (group.decider_matches || []).find((match) => match.id === matchId);
}

function comparedTeamName(score) {
    return score?.ranking_decision?.compared_with_team_name || `Team ${score?.ranking_decision?.compared_with_team_id}`;
}

function directComparisonText(score) {
    const result = score.ranking_decision.direct_comparison_result;
    if (result === 'won') {
        return `Direkter Vergleich gegen ${comparedTeamName(score)} gewonnen.`;
    }
    if (result === 'lost') {
        return `Direkter Vergleich gegen ${comparedTeamName(score)} verloren.`;
    }
    if (result === 'draw') {
        return `Direkter Vergleich gegen ${comparedTeamName(score)} unentschieden.`;
    }
    return 'Direkter Vergleich entscheidet.';
}

function deciderResolvedText(score) {
    const result = score.ranking_decision.hidden_points_result;
    if (result === 'won') {
        return `${score.team.name} hat das Entscheidungsmatch gegen ${comparedTeamName(score)} gewonnen.`;
    }
    if (result === 'lost') {
        return `${score.team.name} hat das Entscheidungsmatch gegen ${comparedTeamName(score)} verloren.`;
    }
    if (result === 'draw') {
        return `Das Entscheidungsmatch gegen ${comparedTeamName(score)} endete unentschieden.`;
    }
    return 'Das Entscheidungsmatch hat den Gleichstand entschieden.';
}

function decisionContent(group, score) {
    const rankingDecision = score.ranking_decision;
    if (!rankingDecision) {
        return '';
    }

    const container = document.createElement('div');
    container.className = 'group-table-modal__decision';

    const message = document.createElement('div');
    message.className = 'group-table-modal__decision-text';

    if (rankingDecision.needs_decider_match) {
        const deciderMatch = rankingDecision.decider_match_id ?
            deciderMatchById(group, rankingDecision.decider_match_id) :
            null;

        if (deciderMatch) {
            if (deciderMatch.state === 'finished') {
                message.textContent = 'Entscheidungsmatch beendet.';
            } else if (deciderMatch.state === 'in_progress') {
                message.textContent = 'Entscheidungsmatch läuft.';
            } else {
                message.textContent = 'Entscheidungsmatch angelegt.';
            }
        } else {
            message.textContent = 'Entscheidungsmatch nötig.';
        }
        container.appendChild(message);

        if (!deciderMatch && score.team.id < rankingDecision.compared_with_team_id) {
            const form = document.createElement('form');
            form.method = 'POST';
            form.action = `/groups/${group.id}/matches`;

            const team1 = document.createElement('input');
            team1.type = 'hidden';
            team1.name = 'team_id_1';
            team1.value = String(score.team.id);
            form.appendChild(team1);

            const team2 = document.createElement('input');
            team2.type = 'hidden';
            team2.name = 'team_id_2';
            team2.value = String(rankingDecision.compared_with_team_id);
            form.appendChild(team2);

            const button = document.createElement('button');
            button.type = 'submit';
            button.className = 'pure-button pure-button-primary group-table-modal__decision-button';
            button.textContent = 'Anlegen';
            form.appendChild(button);

            container.appendChild(form);
        }

        return container;
    }

    if (rankingDecision.resolved_by === 'direct_comparison') {
        message.textContent = directComparisonText(score);
        container.appendChild(message);
        return container;
    }

    if (rankingDecision.resolved_by === 'hidden_points') {
        message.textContent = deciderResolvedText(score);
        container.appendChild(message);
        return container;
    }

    if (rankingDecision.resolved_by === 'tie') {
        message.textContent = `Gleichstand mit ${comparedTeamName(score)}. Kein Entscheidungsmatch nötig.`;
        container.appendChild(message);
        return container;
    }

    return '';
}

function renderGroupTableRows(group) {
    groupTableModalBody.innerHTML = '';

    group.scores.forEach((score) => {
        const row = document.createElement('tr');
        [
            score.position,
            score.team.name,
            score.group_points,
            score.difference_in_points,
            score.scored_points,
        ].forEach((value) => {
            row.appendChild(createCell(value));
        });
        row.appendChild(createCell(decisionContent(group, score)));
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
            renderGroupTableRows(group);
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
