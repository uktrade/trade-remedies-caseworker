accessibleAutocomplete({
    element: document.QuerySelector('#company_search_container'),
    placeholder: "Search",
    autoselect: true,
    id: "input-autocomplete",
    confirmOnBlur: false,
    minLength: 3,
    source: function (query, populateResults) {
        if (query.length < 3) {
            return false
        } else {
            $.ajax({
                type: "GET", url: `/organisationnamesearch?term=${query}`, success: function (data) {
                    if (data) {
                        let names = data.map(result => `${result.title} (${result.company_number})`);
                        proposed_names = Object.fromEntries(data.map(result => [`${result.title} (${result.company_number})`, result]));
                        populateResults(names);
                        if (names.length === 0) {
                            clearCompany();
                        }
                    }
                }, error: function () {

                }
            })
        }
    }
})
