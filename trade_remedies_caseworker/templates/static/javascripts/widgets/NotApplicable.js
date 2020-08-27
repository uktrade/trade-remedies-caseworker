/* Drive the not applicable widget on the actions pages */

define(function () {
  "use strict";
  var constructor = function (el) {
    this.el = el;
    this.outer = el.closest(".form-group");
    this.cbs = this.outer.find("input:not(.na-check)");
    el.on("change", _.bind(onChange, this));
  };

  function onChange() {
    if (this.el.prop("checked")) {
      this.outer.addClass("disabled");
      this.cbs.prop("checked", null).prop("disabled", "disabled");
    } else {
      this.outer.removeClass("disabled");
      this.cbs.prop("disabled", null);
    }
  }
  return constructor;
});
