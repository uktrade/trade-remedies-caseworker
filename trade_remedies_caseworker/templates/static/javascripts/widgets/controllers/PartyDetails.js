// Validate - client-side form validation
define(["vendor/handlebars", "modules/Events"], function (hb, Events) {
  "use strict";
  var constructor = function (el) {
    this.el = el;
    this.case_id = el.attr("data-case-id");
    this.org_id = el.attr("data-org-id");
    this.org_caserole = el.attr("data-caserole");
    new Events().listen("party-updated", _.bind(this.onPartyChange, this));
    this.tabs = this.el.find(".tab-page[data-tab]");
    this.tabs.on("show", _.bind(this.onTabShow, this));
    this.getDuplicates();
  };

  var bannerTemplate = _.template(`
        <div class="column-full">
          <div class="warning">
            <span>There are duplicate versions of this party.</span>
            <button type="button" class="button compact pull-right button-blue modal-form" data-url="/case/<%=case_id%>/organisation/<%=org_id%>/dedupe/" data-event-refresh="party-updated">View/merge duplicates</button>
          </div>
        </div>`);

  constructor.prototype = {
    getDuplicates: function () {
      var self = this;
      $.ajax({
        url: `/organisation/${this.org_id}/duplicates/`,
        method: "GET",
      }).then(function (results) {
        if (results && results.org_matches) {
          self.el
            .find(".duplicate-banner")
            .html(results.org_matches.length > 1 ? bannerTemplate(self) : "")
            .attachWidgets();
        }
      });
    },
    reloadDetails: function (el) {
      // reload the party details section
      var self = this;
      $.ajax({
        url: `/case/${this.case_id}/organisation/${this.org_id}/details/?item=details&template=organisations/_party_details.html`,
        method: "GET",
      }).then(function (results) {
        el.html(results).attachWidgets();
      });
    },
    onTabShow: function (evt) {
      var tab = $(evt.target);
      var pageType = tab.attr("data-tab");
      switch (pageType) {
        case "contacts":
          if (!tab[0].loaded) {
            this.loadContacts(tab);
          }
          break;
      }
    },
    loadContacts: function (el) {
      $.ajax({
        url: `/case/${this.case_id}/organisation/${this.org_id}/details/?item=contacts&caserole=${this.org_caserole}&template=widgets/contact_list_full.html`,
        method: "GET",
      }).then(function (results) {
        if (results.substr(1, 10).indexOf("#32;") >= 0) {
          return; // leave to do it's own thing
        }
        el[0].loaded = true;
        el.html(results).attachWidgets();
      });
    },
    onPartyChange: function (result) {
      var self = this;
      this.getDuplicates();
      this.el
        .find(".contact-list")
        .parent()
        .each(function () {
          self.loadContacts($(this));
        });
      this.reloadDetails(this.el.find(".party-details-area"));
    },
  };
  return constructor;
});
