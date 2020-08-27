// Typeahead - using the jqueryUI autocomplete widget
define(function () {
  "use strict";
  var constructor = function (el) {
    var self = this;
    this.el = el;
    var spl = el.attr("data-revealedby").split(":");
    this.revealField = spl[0];
    this.revealValue = spl[1];
    if (this.revealField) {
      this.form = this.el.parents("form");
      this.activator = this.form.find(this.revealField);
      if (this.activator.length) {
        this.activator.on("change", _.bind(onActivateChange, this));
        this.activator.on("click", _.bind(onActivateChange, this));
        this.activator
          .closest(".form-group")
          .on("click", _.bind(onActivateChange, this));
      }
      onActivateChange.call(this);
    }
  };

  function onActivateChange(evt) {
    var tagName = this.activator.prop("tagName");
    var reveal;
    var value = this.activator.val();
    switch (tagName) {
      case "BUTTON":
        reveal = true;
        break;
      case "INPUT":
        reveal = this.activator.prop("checked");
        break;
      case "SELECT":
        reveal = value == this.revealValue;
    }
    this.el[reveal ? "show" : "hide"]();
    if (!reveal) {
      this.el.find("input[data_hide_value]").each(function () {
        $(this).val($(this).attr("data_hide_value"));
      });
    }
  }

  return constructor;
});
