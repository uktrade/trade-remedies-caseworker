// Typeahead - using the jqueryUI autocomplete widget
define(function () {
  "use strict";
  var constructor = function (el) {
    var self = this;
    this.el = el;
    this.contactForm = el.find("#contact-form");
    this.contactSelector = el.find("#contact-selector");
    this.contactSelector.on("change", _.bind(onActivateChange, this));
    this.contacts = JSON.parse(el.find("#auth-contacts").val());
    onActivateChange.call(this);
  };

  function onActivateChange(evt) {
    var self = this;
    var selectedId = this.contactSelector.val();
    self.contactForm.find("input,textarea").attr("disabled", false).val("");
    _.each(this.contacts, function (contact) {
      if (contact.id == selectedId) {
        var allowEdit = !contact.has_user;
        self.contactForm.find("input,textarea").each(function () {
          var input = $(this);
          name = input.prop("name");
          input.attr("disabled", !allowEdit || name == "email");
          if (name == "org_name") {
            input.val(contact.organisation.name);
          } else {
            input.val(contact[name]);
          }
        });
      }
    });
  }

  return constructor;
});
