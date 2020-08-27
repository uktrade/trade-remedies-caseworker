define(["vendor/handlebars", "modules/Events"], function (hb, Events) {
  "use strict";
  var constructor = function (el) {
    this.el = el;
    this.el.on("click", _.bind(this.onClick, this));
    this.case_id = el.attr("data-case-id");
    new Events().listen("party-updated", _.bind(this.onPartyChange, this));
  };

  constructor.prototype = {
    loadPartial: function loadPartial(partialName) {
      $.ajax({
        url: `/static/javascripts/templates/${partialName}.hbs`,
      }).then(function (result) {
        hb.registerPartial(partialName, result);
      });
    },
    onClick: function onClick(evt) {
      var target = $(evt.target);

      if (target.hasClass("expander")) {
        var outer = target.closest("li");
        if (!outer[0].loaded) {
          outer[0].loaded = true;
          this.loadContacts(outer, target);
        }
      }
    },
    loadContacts: function (el, expander) {
      var org_id = el.attr("data-org-id");
      var org_caserole = el.attr("data-caserole");
      if (!el[0].loaded) {
        el.find(".expand-section .party-list").html(
          `<div class="inner-content"><div class="loading-block"><div>Loading&hellip;</div><div class="progress-bar striped animated pale-blue"></div></div></div>`
        );
      }
      $.ajax({
        url: `/case/${this.case_id}/organisation/${org_id}/details/?item=contacts&caserole=${org_caserole}&template=widgets/contact_list.html`,
        method: "GET",
      }).then(function (results) {
        if (results.substr(1, 10).indexOf("#32;") >= 0) {
          delete el[0].loaded;
          if (expander.hasClass("expanded")) {
            expander.removeClass("expanded");
            el.find(".expand-section")
              .css({ height: 0, display: "none" })
              .removeClass("expanded");
          }
          return; // leave to do it's own thing
        }
        el.find(".expand-section .party-list").html(results).attachWidgets();
      });
    },

    onPartyChange: function (result) {
      var self = this;
      this.el
        .find(".expand-section.expanded")
        .closest("li")
        .each(function () {
          self.loadContacts($(this));
        });
    },
  };

  return constructor;
});
