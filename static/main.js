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
});
