// Typeahead - using the jqueryUI autocomplete widget
define(function () {
  "use strict";
  var constructor = function (el) {
    var self = this;
    this.el = el;
    el.on("mousedown", _.bind(onClick, this));
    el.on("keydown", _.bind(keypress, this));
    var slaveSelector = el.attr("data-slave");
    this.slave = slaveSelector && $(slaveSelector);
    this.storageKey = el.attr("data-storagekey");
    if (this.storageKey) {
      if (window.localStorage[this.storageKey] == "expanded") {
        clickHandler.call(this, true);
      }
    }
  };

  function setHeight() {
    // finds the expanded height of the element
    this.root = this.el.siblings(".expand-section");
    if (!this.root.length) {
      this.root = this.el.parent().siblings(".expand-section");
    }
    if (!this.root.length) {
      this.root = this.el.closest(".expand-base").find(".expand-section");
    }
    this.closedHeight = this.root.height() + "px";
    this.root.css({ height: "auto", display: "block" });
    this.rootHeight = this.root.height() + "px";
    this.root.css({ height: this.closedHeight });
  }

  function keypress(evt) {
    if (evt.keyCode == 13) {
      clickHandler.call(this);
    }
  }

  function onClick(evt) {
    if (evt.button == 0) {
      if (quenched) {
        return;
      }
      quenched = true;
      evt.preventDefault();
      evt.stopImmediatePropagation();
      clickHandler.call(this);
    }
  }

  var quenched = false;

  function clickHandler(fast) {
    var self = this;
    if (!self.root) {
      setHeight.call(self);
    }
    self.root.css({ transition: `height ${fast ? "0" : "0.3s"}` });
    this.slave &&
      this.slave.css({ transition: `margin-top ${fast ? "0" : "0.3s"}` });
    self.expanded = !self.el.hasClass("expanded");
    if (self.storageKey) {
      window.localStorage[self.storageKey] = self.expanded
        ? "expanded"
        : "collapsed";
    }
    self.el[self.expanded ? "addClass" : "removeClass"]("expanded");
    self.root[self.expanded ? "addClass" : "removeClass"]("expanded");
    //self.slave && self.slave.addClass('slow-move');
    if (self.expanded) {
      self.root.css({ display: "block" });
      setTimeout(function () {
        self.root.css({
          height: self.rootHeight,
          overflow: "hidden",
          display: "block",
        });
        self.slave && self.slave.css({ marginTop: self.rootHeight });
      }, 0);
      setTimeout(function () {
        quenched = false;
        self.root.css({ height: "auto" });
      }, 300);
      self.root.trigger("show");
    } else {
      this.rootHeight = this.root.height() + "px";
      self.root.css({ height: this.rootHeight });
      setTimeout(function () {
        self.root.css({ height: self.closedHeight });
        self.slave && self.slave.css({ marginTop: "0px" });
      }, 0);
      setTimeout(function () {
        quenched = false;
        self.root.css({ display: "none" });
      }, 300);
    }
  }

  return constructor;
});
