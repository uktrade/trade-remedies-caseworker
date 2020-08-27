// A simple one-way reveal on the click of a button

define(function () {
  "use strict";
  var constructor = function (el) {
    var self = this;
    this.el = el;
    this.selector = el.attr("data-reveals");
    if (this.selector) {
      this.form = this.el.parents("form");
      this.revealEl = this.form.find(this.selector);
      this.el.on("click", _.bind(onClick, this));
    }
  };

  function onClick(evt) {
    this.revealEl.removeClass("hidden").show();
  }

  return constructor;
});
