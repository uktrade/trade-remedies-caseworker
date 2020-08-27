// expand a drop-down menu
define([], function () {
  "use strict";

  function constructor(el) {
    // Toggle the edit section
    var self = this;
    self.menu = el.siblings(".function-menu");
    self.menu.css({ display: "block" });
    self.menuHeight = self.menu.height();
    self.menu.css({ height: "0px" });
    el.on("click", _.bind(onClick, this));
    self.bodyClick = _.bind(bodyClick, this);
  }

  function onClick(evt) {
    var self = this;
    evt.preventDefault();
    this.menu.css({ height: this.menuHeight + "px" });
    setTimeout(function () {
      $(document.body).on("click", self.bodyClick);
    }, 0);
  }

  function bodyClick() {
    $(document.body).off("click", this.bodyClick);
    this.menu.css({ height: "0" });
  }
  return constructor;
});
