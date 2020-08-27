// widget to upload a file
define(function () {
  "use strict";

  var instance;

  var constructor = function (el) {
    var self = this;
    $(document.body).on("click", _.bind(onClick, this));
    $(document.body).on("keydown", _.bind(onKeydown, this));
  };

  var inClick;

  function onClick(evt) {
    var self = this;
    // This allows click-handlers to prevent further copies of themselves running
    if (self.quench) return;
    var target = $(evt.target);
    var popupTrigger = target.closest(".js-pop-up");
    if (popupTrigger.length) {
      var content = popupTrigger.parent().find(".js-pop-up-content").html();
      if (content) {
        evt.preventDefault();
        var title = popupTrigger.parent().find(".js-pop-up-title").html();
        require(["modules/Lightbox"], function (Lightbox) {
          self.dlg = new Lightbox({
            title: title || "Details",
            message: content,
            buttons: { close: 1 },
          });
          self.dlg.getContainer().attachWidgets();
        });
      }
    }
    var handler = target.closest("[data-handler]").attr("data-handler");
    if (handler) {
      if (handler in { clickConfirm: 1, menuExpand: 1, carousel: 1 }) {
        //TODO: This is a bodge but how to do it better?
        evt.preventDefault();
      }
      require(["clickhandlers/" + handler], function (module) {
        new module(target.closest("[data-handler]"), self);
      });
      return true;
    }
  }

  function onKeydown(evt) {
    var self = this;
    // This allows click-handlers to prevent further copies of themselves running
    if (evt.keyCode != 13) return;
    if (self.quench) return;
    var target = $(evt.target);
    var handler = target.closest("[data-handler]").attr("data-handler");
    if (handler) {
      evt.preventDefault(); // this will stop an extra click event from firing on a button
      require(["clickhandlers/" + handler], function (module) {
        new module(target.closest("[data-handler]"), self);
      });
    }
  }

  window.confirmPopup = function (message, title) {
    return new Promise(function (resolve, reject) {
      require(["modules/Lightbox"], function (Lightbox) {
        var lb = new Lightbox({
          title: title || "Confirm",
          message: message,
          buttons: { ok: 1, cancel: 1 },
        });
        lb.getContainer()
          .find("button")
          .on("click", function (evt) {
            if ($(evt.target).val() == "ok") {
              resolve();
            } else {
              reject();
            }
          });
      });
    });
  };

  return constructor;
});
