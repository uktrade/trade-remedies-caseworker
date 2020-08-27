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
      var message;
      if ((message = target.attr("data-message"))) {
        // it needs a confirm box before trigger
        require(["modules/popUps"], function (popups) {
          popups
            .confirm(message, target.attr("data-message") || "Confirm")
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
