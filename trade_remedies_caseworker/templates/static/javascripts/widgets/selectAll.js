// Support a 'select all' checkbox
// Attach the handler to the 'all' checkbox
// put class 'select-container' around the outside to emcompass all applicable checkboxes, otherwise default to body
// add a data-selectkey if you want several sets of checkboxes within a container.
// place an element with a class 'select-count' next to the input and it will be written with the count of selected items

define([], function () {
  "use strict";

  function constructor(el) {
    this.container = el.closest(".select-container");
    if (!this.container.length) {
      this.container = $(document.body);
    }
    this.selectKey = el.attr("data-selectkey");
    if (this.selectKey) {
      this.checkboxes = this.container
        .find("input[type=checkbox][data-selectkey=" + this.selectKey + "]")
        .filter(":not([value=all])");
    } else {
      this.checkboxes = this.container
        .find("input[type=checkbox]")
        .filter(":not([value=all])");
    }
    this.trigger = el;
    this.container.on("change", _.bind(onChange, this));
    this.countContainer = el.siblings(".select-count");
    if (!this.countContainer.length) {
      this.countContainer = el.parent().siblings(".select-count");
    }
    correctTrigger.call(this);
  }

  function correctTrigger() {
    // Sets the driving checkbox based on the others
    var count = 0;
    this.checkboxes.each(function () {
      if ($(this).prop("checked")) {
        count += 1;
      }
    });
    this.trigger.prop(
      "checked",
      count == this.checkboxes.length ? "checked" : false
    );
    //var text = (count > 0 ? (count+' of ') : '')+this.checkboxes.length;
    var text = count + " of " + this.checkboxes.length;
    this.countContainer.text(text);
  }

  function onChange(evt) {
    var target = $(evt.target);
    if (target[0] == this.trigger[0]) {
      // set or clear all boxes
      if (target.prop("checked")) {
        this.checkboxes.prop("checked", "checked");
      } else {
        this.checkboxes.prop("checked", false);
      }
    }
    correctTrigger.call(this);
  }
  return constructor;
});
