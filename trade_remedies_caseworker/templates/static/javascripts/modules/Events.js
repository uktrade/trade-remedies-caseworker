// widget to upload a file
define(function () {
  "use strict";

  var constructor = function (el) {
    var self = this;
    this.eventList = document.body.eventList = document.body.eventList || {};
  };

  constructor.prototype = {
    listen: function (event, handler) {
      (this.eventList[event] = this.eventList[event] || []).push(handler);
    },
    fire: function (event, context) {
      var listeners = this.eventList[event] || [];
      _.each(listeners, function (handler) {
        handler(context);
      });
    },
  };

  return constructor;
});
