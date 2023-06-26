// Typeahead - using the jqueryUI autocomplete widget
define(["modules/helpers", "modules/popUps", "modules/Events"], function (
  helpers,
  popups,
  Events
) {
  "use strict";

  var constructor = function (el) {
    this.el = el;
    this.url = this.el.attr("data-url") || this.el.attr("href");
    // provide target block rather than lightbox
    var target_block = this.el.attr("data-target-block");
    this.target_block = target_block && $(target_block);
    this.update_event = this.el.attr("data-event-update");
    this.refresh_event = this.el.attr("data-event-refresh");
    this.open_by_detault = this.el.attr("data-open-by-default");
    if (this.refresh_event) {
      new Events().listen(this.refresh_event, _.bind(this.loadContent, this));
    }
    // provide block as source for the modal
    var blockId = el.attr("data-block-id");
    if (blockId) {
      this.element = $("#" + blockId);
    }
    if (this.url || this.element) {
      el.on("click", _.bind(onClick, this));
        if (this.open_by_detault) {
          this.openWindow();
        }
    } else {
      console.error("Modal url not found", el);
    }
  };
  var semaphore;

  function showErrors(errors) {
    var outer = this.dlg.$outer;
    outer.find(".form-group-error").removeClass("form-group-error");
    outer.find(".error-message").remove();
    _.each(errors, function (message, name) {
      var input = outer.find("[name=" + name + "]");
      var group = input.closest(".form-group");
      group.addClass("form-group-error");
      group
        .find("label")
        .first()
        .append(
          '\
                <span class="error-message">' +
            message +
            "</span>\
            "
        );
    });
  }

  function formSubmit(evt) {
    //        if(semaphore) return;
    var self = this;
    evt.preventDefault();
    var form = evt.target;
    var submitMode = $(form).attr("data-submit-mode");
    var alertMsg = self.el.attr("data-alert");
    if (!(form.validate || _.noop)()) {
      var data = $(form)
        .find("input[type=hidden],:input:not(:hidden),button")
        .serializeArray();
      // get the clicked button and add to the form data
      var active = $(document.activeElement);
      if (active.length) {
        data.push({ name: active.attr("name"), value: active.val() });
      }
      $.ajax({
        method: $(form).attr("method") || "POST",
        url: $(form).attr("action"),
        data: data,
        //dataType: 'json'
      }).then(
        function (result) {
          if (_.isString(result)) {
            try {
              result = JSON.parse(result);
            } catch (e) {
              if (result.substr(1, 10).indexOf("#32;") == -1) {
                // only replace content if it's not a login
                $(form).html(result);
                $(form).attachWidgets();
              }
              return;
            }
          }
          if (result.error) {
            popups.error(result.error, "Error");
          } else if (result.errors) {
            showErrors.call(self, result.errors);
          } else if (result.redirect_url) {
            alertMsg = result.alert || alertMsg;
            // show alert as an Alert box.
            if (result.pop_alert && alertMsg) {
              alert(alertMsg);
            }
            location.assign(
              result.redirect_url + (alertMsg ? "?alert=" + alertMsg : "")
            );
          } else if (result.content) {
            // this is not used yet
            self.form.html(result.content);
            self.form.attachWidgets();
          } else {
            if (self.update_event) {
              self.dlg.close();
              new Events().fire(self.update_event, self);
            } else {
              window.location.reload();
            }
          }
        },
        function (xhs) {
          // The response is not json, so just reload the page
          window.location.assign(window.location.pathname);
          console.error("Modal response", xhs);
        }
      );
    }
  }

  function onClick(evt) {
    evt.preventDefault();
    this.openWindow();
  }

  constructor.prototype = {
    openWindow: function () {
      var self = this;
      require(["modules/Lightbox"], function (Lightbox) {
        if (self.url) {
          // Get the url again in case it's been changed.  Bundle-builder does that!
          self.url = self.el.attr("data-url") || self.el.attr("href");
          self.dlg = new Lightbox({
            title: "",
            content:
              '<div class="inner-content"><div class="loading-block"><div>Loading&hellip;</div><div class="progress-bar striped animated"></div></div></div>',
            buttons: { ok: 1, cancel: 1 },
            //nonmodal: true,
          });
          self.loadContent();
        }
        if (self.element && self.element.length) {
          // grab hidden element
          self.dlg = new Lightbox({
            title: "",
            content: self.element.html(),
            buttons: { ok: 1, cancel: 1 },
          });
          self.el.removeAttr("disabled"); // in case it's been disabled by debounce
        }
      });
    },

    loadContent: function () {
      var self = this;
      $.ajax({
        url: self.url,
        method: "get",
      }).then(
        function (res) {
          self.el.removeAttr("disabled"); // in case it's been disabled by debounce
          if (_.isString(res)) {
            try {
              res = JSON.parse(res);
            } catch (e) {}
          }
          if (_.isString(res)) {
            if (res.substr(1, 10).indexOf("#32;") >= 0) {
              if (self.dlg) {
                self.dlg.close();
              }
            } else {
              if (self.target_block) {
                self.target_block.html("");
                self.target_block.append($(res));
                self.target_block.attachWidgets();
                self.target_block.parent().addClass("show-block");
                self.target_block.on("click", function (evt) {
                  var target = $(evt.target);
                  if (target.hasClass("dlg-close")) {
                    self.target_block.parent().removeClass("show-block");
                  }
                });
                if (
                  self.target_block.find("form").attr("data-submit-mode") !=
                  "browser"
                ) {
                  self.target_block
                    .find("form")
                    .on("submit", _.bind(formSubmit, self));
                }
                self.el.removeAttr("disabled"); // kill the debounce
              } else {
                if (self.dlg) {
                  var container = self.dlg.getContainer();
                  container.find(".outer").html(res);
                  container.attachWidgets();
                  if (
                    container.find("form").attr("data-submit-mode") != "browser"
                  ) {
                    container
                      .find("form")
                      .on("submit", _.bind(formSubmit, self));
                  }
                }
              }
            }
          } else {
            if (res.error) {
              popups.error(res.error, "Error");
            }
            if (self.dlg) {
              self.dlg.close();
            }
          }
        },
        function (res, res2) {
          self.el.removeAttr("disabled"); // in case it's been disabled by debounce
          if (res.status == 403) {
            window.location.assign(window.location.pathname); // If the user is logged out, reload the page which will be redirected to the loging page
          } else {
            popups.error(res.statusText).then(function () {
              self.dlg.close();
            });
          }
        }
      );
    },
  };
  return constructor;
});
