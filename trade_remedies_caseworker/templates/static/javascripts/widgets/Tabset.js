define(function () {
  "use strict";
  var constructor = function (el) {
    var self = this;
    this.el = el;
    this.tabPages = this.el.find(".tab-page[data-tab]");
    this.tabPageIdx = {};
    this.tabPages.each(function () {
      var tabKey = $(this).attr("data-tab");
      self.tabPageIdx[tabKey] = $(this);
    });
    this.el
      .find(".tabset")
      .on("click", _.bind(onClick, this))
      .on("mousedown", _.bind(onClick, this));
  };

  function mouseDown(evt) {
    if ($(evt.target).closest(".tab")) {
      evt.preventDefault(); // stop the tab from focussing
    }
  }

  function onClick(evt) {
    evt.preventDefault();
    var tab = $(evt.target).closest(".tab");
    var tabKey = tab.find("a").attr("data-tab");
    if (tabKey) {
      this.el.find(".selected").removeClass("selected");
      tab.addClass("selected");
      this.tabPages.addClass("hidden");
      this.tabPageIdx[tabKey].removeClass("hidden");
      this.tabPageIdx[tabKey].trigger("show");
    }
  }

  return constructor;
});
