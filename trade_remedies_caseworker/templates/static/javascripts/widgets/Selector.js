define(function () {
  "use strict";
  var constructor = function (el) {
    this.el = el;
    _.bindAll(this, "onClick", "bodyClick");
    this.el.on("click", this.onClick);
    this.picker = $(this.el.attr("data-picker"));
    this.el.css({ cursor: "pointer", position: "relative" });
    this.hidden = this.el.siblings("input[type=hidden]");
  };

  constructor.prototype = {
    openPicker: function () {
      this.el.after(this.picker);
      this.updateSelected(this.hidden.val());
      this.picker.removeClass("hidden").addClass("popout");
      $(document.body).on("click", this.bodyClick);
    },
    updateSelected: function (val) {
      this.picker.find("[value]").each(function () {
        var el = $(this);
        el.removeClass("selected");
        if (val == el.attr("value")) {
          el.addClass("selected");
        }
      });
    },
    closePicker: function () {
      this.picker.addClass("hidden");
      $(document.body).off("click", this.bodyClick);
    },
    onClick: function (evt) {
      this.openPicker();
      evt.stopPropagation();
    },
    bodyClick: function (evt) {
      var target = $(evt.target);
      if (target.closest(".popout").length) {
        var val = target.closest(".option").attr("value");
        this.hidden.val(val);
        // todo - needs to be generic somehow - change the activation element
        this.el.css({ backgroundColor: val });
      }
      this.closePicker();
    },
  };

  return constructor;
});
