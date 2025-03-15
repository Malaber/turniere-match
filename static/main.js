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
