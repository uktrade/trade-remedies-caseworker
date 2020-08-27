// Make an inset scroll shadow, only if the region is scrolled
define(function () {
  "use strict";
  var constructor = function (el) {
    this.el = el;
    this.el.on("scroll", _.bind(onScroll, this));
  };

  function onScroll(evt) {
    this.el.setClass("scroll-shadow", this.el[0].scrollTop != 0);
    this.el.setClass("scroll-shadow-left", this.el[0].scrollLeft != 0);
  }

  return constructor;
});
