// On the add organisation form, see if the org details match and populate a pop-up
define(["modules/popUps"], function (popups) {
  "use strict";

  function constructor(el) {
    this.form = el.closest("form");
    this.form.on("click", _.bind(onClick, this));
  }

  function getFormValues() {
    var populated = {};
    var errors;
    if (this.form[0].validate) {
      errors = this.form[0].validate();
    }
    _.each(this.form.serializeArray(true), function (item) {
      populated[item.name] = item.value;
    });
    return {
      values: populated,
      errors: errors,
    };
  }

  function onClick(evt) {
    var target = $(evt.target);
    var action = target.attr("data-action");
    if (target.hasClass("lookup")) {
      lookupOrg.call(this);
    }
    if (action == "picked_organisation") {
      var values = getFormValues.call(this).values;
      var carouselEl = this.form.find(".carousel-surround");
      this.carousel = carouselEl[0].carousel;
      var partyCard = this.carousel.selectedCard;
      var partyId = partyCard && partyCard.attr("data-party-id");
      if (partyId) {
        $.ajax({
          method: "POST",
          url: this.form.attr("action"),
          data: {
            csrfmiddlewaretoken: window.dit.csrfToken,
            organisation_id: partyId,
          },
        }).then(
          function (result) {
            if (result.redirect_url) {
              window.location.replace(result.redirect_url);
            }
          },
          function (result) {
            window.location.reload();
          }
        );
      }
    }
    if (action == "create_organisation") {
      var values = getFormValues.call(this).values;
      values["csrfmiddlewaretoken"] = window.dit.csrfToken;
      $.ajax({
        method: "POST",
        url: this.form.attr("action"),
        data: values,
      }).then(
        function (result) {
          if (result.redirect_url) {
            window.location.replace(result.redirect_url);
          }
        },
        function (result) {
          popups.alert("Failed to create organisation", "Error");
        }
      );
    }
  }

  function lookupOrg() {
    var self = this;
    var data = getFormValues.call(this);
    var values = data.values;
    // Fire request to search for matching company
    if (!data.errors) {
      $.ajax({
        method: "GET",
        url: "/organisations/match/",
        data: {
          organisation_name: data.values.organisation_name,
          companies_house_id: data.values.companies_house_id,
        },
      }).then(
        function (result) {
          self.form.find(".page").addClass("hidden");
          if (result.indexOf("No matching") > 0) {
            self.form.find(".page-3").removeClass("hidden");
          } else {
            self.form
              .find(".org-search-results")
              .html(result)
              .attachWidgets()
              .closest(".page")
              .removeClass("hidden");
          }
        },
        function () {
          debugger;
        }
      );
    }
  }

  return constructor;
});
