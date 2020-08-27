/* Click confirm

On click on a button or link, fire up a confirm with the text from 'data-confirmtext'
If OK, the click is re-fired on the element

*/
define(["modules/popUps"], function (popups) {
  "use strict";

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

  function redirectOrReload(url) {
    if (url == "reload") {
      location.reload();
    } else {
      location.assign(url);
    }
  }

  function constructor(el, manager) {
    var message = el.attr("data-message") || "Are you sure?";
    var title = el.attr("data-title") || "Confirm action?";
    var name = el.attr("name");
    var value = el.attr("value");
    setTimeout(function () {
      // This is to restore the button if the debounce disables it.
      el.removeAttr("disabled");
    }, 0);
    popups.confirm(message, title).then(function () {
      var url = el.attr("data-url");
      if (url) {
        $.ajax({
          method: "POST",
          url: url,
          data: { csrfmiddlewaretoken: window.dit.csrfToken },
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
              var alert = result.alert || alert;
              if (alert) {
                popups.alert(alert).then(function () {
                  redirectOrReload(result.redirect_url);
                });
              } else {
                redirectOrReload(result.redirect_url);
              }
            }
          },
          function () {
            popups.error("Failed to save data", "Error");
          }
        );
      } else {
        manager.quench = true;
        if (name) {
          var hiddenEl = $(
            '<input type="hidden" name="' + name + '" value="' + value + '">'
          );
          el.after(hiddenEl);
        }
        el.trigger("click");
        hiddenEl && hiddenEl.remove();
        manager.quench = false;
      }
    });
  }

  return constructor;
});
