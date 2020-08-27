define(function () {
  "use strict";
  var constructor = function (el) {
    var self = this;
    self.el = el;
    el.css({ width: 0, height: 0, opacity: 0, position: "absolute" });
    var strDisabled = el.attr("disabled") ? 'disabled="1"' : "";
    var strShowpicker = el.attr("disabled") ? "hidden" : "";
    self.boxmode = el.attr("data-boxmode");
    if (!el[0].datepicker) {
      var parsedDate = Date.parseIso(self.el.val());
      if (true || self.boxmode) {
        self.hiddenEl = $(`
					<div class="date-widget">
	                  <input class="form-control date" data-part="0" type="number" pattern="[0-9]*" value="${
                      parsedDate && parsedDate.format("dd")
                    }" ${strDisabled}>
	                  <input class="form-control month" data-part="1" type="number" pattern="[0-9]*" value="${
                      parsedDate && parsedDate.format("mm")
                    }" ${strDisabled}>
	                  <input class="form-control year" data-part="2" type="number" pattern="[0-9]*" value="${
                      parsedDate && parsedDate.format("yyyy")
                    }" ${strDisabled}>
						<div class="icon-calendar datepicker-trigger ${strShowpicker}">
							<input type="text" class="us-format" style="width:0;height:0;border:none;outline:none;opacity:0;" value="${
                parsedDate && parsedDate.format("mm/dd/yyyy")
              }">
						</div>
					</div>`);
      } else {
        self.hiddenEl = $(`
						<div class="date-widget">
							<span>${parsedDate && parsedDate.format("dd mon yyyy")}</span>
						<div class="icon-calendar datepicker-trigger ${strShowpicker}">
							<input type="text" class="us-format" style="width:0;height:0;border:none;outline:none;opacity:0;" value="${
                parsedDate && parsedDate.format("mm/dd/yyyy")
              }">
						</div>
						</div>
					`);
      }

      el.after(self.hiddenEl);
      require(["jqui/widgets/datepicker"], function (datepicker) {
        self.outputEl = self.hiddenEl.find("input.form-control");
        self.datePickerEl = self.hiddenEl.find("input.us-format");
        self.datePickerEl.datepicker({ changeMonth: true, changeYear: true });
        self.hiddenEl.find(".datepicker-trigger").on("click", function () {
          self.datePickerEl.focus();
        });
        self.datePickerEl.on("change", _.bind(self.onPickChange, self));
        self.outputEl.on("change", _.bind(self.onTextChange, self));
      });
    }
  };

  var formatStrings = ["dd", "mm", "yyyy"];

  constructor.prototype = {
    dateFromBoxes: function () {
      var a = [];
      this.outputEl.each(function () {
        var el = $(this);
        var part = el.attr("data-part");
        a[part - 0] = el.val();
      });
      return Date.parseIso(`${a[2]}-${a[1]}-${a[0]}T00:00:00Z`);
    },

    populateBoxes: function (date) {
      if (!date) {
        this.el.val("");
        this.outputEl.val("");
        return;
      }
      this.datePickerEl.val(date.format("mm/dd/yyyy"));
      this.el.val(date.toISOString());
      this.outputEl.each(function () {
        var el = $(this);
        var part = el.attr("data-part") - 0;
        el.val(date.format(formatStrings[part]));
      });
    },

    onTextChange: function () {
      var date = this.dateFromBoxes();
      this.populateBoxes(date);
    },

    _change: function () {
      var parsedDate = Date.parseIso(this.el.val());
      this.populateBoxes(parsedDate);
    },

    onPickChange: function () {
      var dateSplit = /(\d{2})\/(\d{2})\/(\d{4})/.exec(this.datePickerEl.val());
      var date = new Date(
        `${dateSplit[3]}-${dateSplit[1]}-${dateSplit[2]}T00:00:00`
      );
      this.populateBoxes(date);
    },
  };
  return constructor;
});
