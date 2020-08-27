// Typeahead - using the jqueryUI autocomplete widget
define(function (Events) {
  "use strict";

  var pollPeriod = 5000;
  var regex = /data-attach\=\"VirusCheckRefesh\"/;

  var constructor = function (el) {
    this.el = el;
    this.timerDone = _.bind(timerDone, this);
    setTimeout(this.timerDone, pollPeriod);
  };

  function timerDone() {
    var self = this;
    var data = {
      csrfmiddlewaretoken: window.dit.csrfToken,
    };
    $.ajax({
      method: "GET",
      url: window.location.href,
    }).then(function (result) {
      if (regex.test(result)) {
        setTimeout(self.timerDone, pollPeriod);
      } else {
        window.location.reload();
      }
    });
  }

  return constructor;
});
