define(function () {
  "use strict";
  var constructor = function (el) {
    $(el).on("submit", onSubmit);
  };

  function onSubmit(evt) {
    evt.preventDefault();
    var form = $(evt.target);
    form.append(window.dit.csrfToken_input);
    var data = form.serialize();
    var url = form.attr("action");
    var method = form.attr("method") || "post";
    form.find("button[type=submit]").prop("disabled", "disabled");
    $.ajax({
      url: url,
      method: method,
      data: data,
    }).then(
      function (result) {
        if (result.error) {
          popups.error(result.error, "Error");
        } else if (result.errors) {
          showErrors.call(self, result.errors);
        } else if (result.redirect_url) {
          location.assign(result.redirect_url);
        } else {
          window.location.assign(window.location.pathname); // strip off any search string there may be
        }
      },
      function (err) {
        debugger;
      }
    );
  }
  return constructor;
});
