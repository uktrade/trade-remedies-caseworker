// Functions to easily initialise a company searcher autocomplete widget that scrapes the DB for company names

function initialise_company_searcher(company_search_container, selected_company_wrapper, selected_company, selected_company_hidden_input) {
    let proposed_names = {};
    accessibleAutocomplete({
        element: company_search_container[0],
        placeholder: "Search",
        id: company_search_container.attr("id"),
        autoselect: true,
        minLength: 3,
        source: function (query, populateResults) {
            $.ajax({
                url: `/organisationname/search?term=${query}&ignore_case_count=yes`,
                success: function (data) {
                    if (data.organisations) {
                        let names = data.organisations.map(result => `${result.name} (${result.companies_house_id})`);
                        proposed_names = Object.fromEntries(data.organisations.map(result => [`${result.name} (${result.companies_house_id})`, result]));
                        populateResults(names);
                    } else {
                    }
                }
            })
        },
        onConfirm: function (confirmed_name) {
            if (typeof (confirmed_name) !== "undefined") {
                if (confirmed_name in proposed_names) {
                    let company_data = proposed_names[confirmed_name];
                    selected_company_wrapper.show();
                    selected_company.text(`${company_data.name} (${company_data.companies_house_id}) ${company_data.address}`);
                    selected_company_hidden_input.val(company_data.id);
                    return true;
                }
                selected_company_wrapper.hide();
                selected_company.text('');
            }
        }
    })
}
