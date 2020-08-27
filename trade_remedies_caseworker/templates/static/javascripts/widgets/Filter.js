define(function () {
  "use strict";
  /* 
	Filter - drives the party filter to hide/show rows from party selector
	Usage: 
		add data-filterkey to checkboxes in the filter block.
		add data-filteritem to elements to hide/show
*/

  var constructor = function (el) {
    this.container = el;
    var self = this;
    this.filters = el.find("[data-filterkey]");
    el.on("change", _.bind(onChange, this));
  };

  function onChange(evt) {
    var target = $(evt.target);
    var key = target.attr("data-filterkey");
    var filter = {};

    if (key) {
      // get all filter values
      this.filters.each(function () {
        var row = $(this);
        if (row.prop("checked")) {
          var key = row.attr("data-filterkey");
          filter[key] = 1;
        }
      });
      var any = _.keys(filter).length == 0;
      this.container.find("[data-filteritem]").each(function () {
        var line = $(this);
        var key = line.attr("data-filteritem");
        line[any || key in filter ? "show" : "hide"]();
      });
    }
  }

  return constructor;
});
