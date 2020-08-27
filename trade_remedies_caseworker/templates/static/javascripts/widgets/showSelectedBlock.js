// Based off a select, show/hide corresponding blocks.
//This is used on the document download selector for the LOA verify page

define([], function () {
  "use strict";

  function constructor(el) {
    this.el = el;
    this.download_link = el.siblings("a");
    el.on("change", _.bind(onChange, this));
    onChange.call(this);
  }

  function onChange(evt) {
    var value = this.el.val();
    var href = this.el.children("option:selected").attr("data-downloadlink");
    this.download_link.attr({ href: href, disabled: href ? false : true });
  }

  return constructor;
});
