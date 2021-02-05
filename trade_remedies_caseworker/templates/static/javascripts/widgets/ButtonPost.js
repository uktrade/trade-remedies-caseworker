// Typeahead - using the jqueryUI autocomplete widget
define(["modules/Events"], function (Events) {
  "use strict";

  var constructor = function (el) {
    this.el = el;
    el.on("click", _.bind(onClick, this));
  };

  function postQuery(el) {
    var data = {
      csrfmiddlewaretoken: window.dit.csrfToken,
    };
    $.ajax({
      method: el.attr("data-method") || "POST",
      url: el.attr("data-url") || target.attr("href"),
      data: data,
      //dataType: 'json'
    }).then(function (result) {
      var event;
      if ((event = el.attr("data-event"))) {
        new Events().fire(event, result);
      }
    });
  }

  function onClick(evt) {
    var self = this;
    var target = $(evt.target);
    if (target.attr("data-method")) {
      var message = target.attr("data-message") || "Are you sure?";
      var title = target.attr("data-title") || "Confirm action";
      if (message) {
        // it needs a confirm box before trigger
        require(["modules/popUps"], function (popups) {
          popups
            .confirm(target.attr("data-message"), title)
            .then(function () {
              postQuery.call(self, target);
            });
        });
      } else {
        postQuery.call(self, target);
      }
    }
  }

  return constructor;
});
