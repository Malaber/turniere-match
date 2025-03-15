function filterTeams() {
    const input = document.getElementById("teamSearch");
    const filter = input.value.toUpperCase();
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

// Focus search input on page load
document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('teamSearch').focus();
});

// Shortcut to focus search input with cmd/ctrl + k
document.addEventListener('keydown', function(event) {
    if ((event.metaKey || event.ctrlKey) && event.key === 'k') {
        event.preventDefault();
        document.getElementById('teamSearch').focus();
    }
});