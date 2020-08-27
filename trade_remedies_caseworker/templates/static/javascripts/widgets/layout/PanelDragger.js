define(["modules/Events"], function (Events) {
  "use strict";

  var collapsedWidth = 15;

  var constructor = function (el) {
    this.el = el;
    this.leftMode = el.attr("data-mode") != "right";
    _.bindAll(
      this,
      "mouseMove",
      "mouseDown",
      "pointerDown",
      "mouseUp",
      "check"
    );
    this.slavePanel = $(el.attr("data-slavepanel"));
    el.on("mousedown", this.mouseDown);
    el.on("pointerdown", this.pointerDown);
    this.dragPanel = el.closest(".drag-panel");
    this.handle = this.el.find(".handle");
    this.id = this.dragPanel.attr("id");
    this.offsetParent = this.dragPanel.offsetParent();
    var width = (window.localStorage["drag_" + this.id] || 0) - 0;
    this.collapsed = window.localStorage["open_" + this.id] != "y";
    if (this.collapsed) {
      this.setCollapse(this.collapsed, true);
    } else {
      this.setWidth(width);
    }
    $(window).on("resize", this.check);
  };

  constructor.prototype = {
    setWidth: function (width) {
      width = Math.max(width, collapsedWidth);
      width = Math.min(this.offsetParent.width() - collapsedWidth, width);
      this.width = width;
      if (this.leftMode) {
        this.dragPanel.css({ width: width + "px" });
        this.slavePanel.css({ left: width + "px" });
      } else {
        this.dragPanel.css({ width: width + "px" });
        this.slavePanel.css({ right: width + "px" });
      }
    },

    setCollapse: function (collapse, fast) {
      var self = this;
      var changed = collapse != this.collapsed;
      this.collapsed = collapse;
      this.handle.setClass("collapsed", this.collapsed);
      this.dragPanel.setClass("panel-collapsed", this.collapsed);
      window.localStorage["open_" + this.id] = this.collapsed ? "n" : "y";
      var width = this.collapsed
        ? collapsedWidth
        : window.localStorage["drag_" + this.id] || 500;
      if (fast) {
        this.setWidth(width);
      } else {
        this.dragPanel.addClass("slow-move");
        this.slavePanel.addClass("slow-move");
        this.setWidth(width);
        window.setTimeout(function () {
          self.dragPanel.removeClass("slow-move");
          self.slavePanel.removeClass("slow-move");
        }, 300);
      }
      if (changed) {
        new Events().fire("panel-collapse", this.collapsed);
      }
    },

    check: function () {
      // on a resize of the container - check that we are still within limits
      this.setWidth(this.width);
    },

    pointerDown: function (pe) {
      var evt = pe.originalEvent;
      if ($(evt.target).hasClass("handle")) {
        return;
      }
      this.el[0].setPointerCapture(evt.pointerId);
      this.pointerId = evt.pointerId;
    },

    mouseDown: function (evt) {
      evt.preventDefault(); // to prevent drag selection of text
      evt.stopPropagation();
      if ($(evt.target).hasClass("handle")) {
        this.setCollapse(!this.collapsed);
        return;
      }
      this.startX = evt.clientX;
      this.el.on("mousemove", this.mouseMove);
      this.el.on("mouseup", this.mouseUp);
      //this.el[0].setPointerCapture(evt);
      this.startPanelWidth = this.dragPanel.width();
    },

    mouseMove: function (evt) {
      var offX = evt.clientX - this.startX;
      var width;
      if (this.leftMode) {
        width = this.startPanelWidth - 0 + offX;
      } else {
        width = this.startPanelWidth - 0 - offX;
      }
      if (this.collapsed) {
        this.setCollapse(false);
      }
      this.setWidth(width);
    },

    mouseUp: function (evt) {
      this.el[0].releasePointerCapture(this.pointerId);
      this.el.off("mousemove", this.mouseMove);
      this.el.off("mouseup", this.mouseUp);
      var width = this.dragPanel.width();
      if (width > collapsedWidth) {
        window.localStorage["drag_" + this.id] = this.dragPanel.width();
      } else {
        this.setCollapse(true);
      }
    },
  };

  return constructor;
});
