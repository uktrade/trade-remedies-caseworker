// Page controller for the caseworker hub page
define(["modules/helpers", "modules/popUps"], function (helpers, popups) {
  "use strict";

  var tpForm = _.template(
    '\
        <h2 class="heading-medium">Set due date</h2>\
        <form autocomplete="off">\
          <div class="form-group">\
            <fieldset>\
              <div class="form-date">\
                <div class="form-group form-group-day">\
                  <label class="form-label" for="due-day">Day</label>\
                  <input class="form-control" id="due-day" name="day" type="number" pattern="[0-9]*" value="<%=submission.due_at && submission.due_at[3] %>">\
                </div>\
                <div class="form-group form-group-month">\
                  <label class="form-label" for="due-month">Month</label>\
                  <input class="form-control" id="due-month" name="month" type="number" pattern="[0-9]*" value="<%=submission.due_at && submission.due_at[2] %>">\
                </div>\
                <div class="form-group form-group-year">\
                  <label class="form-label" for="due-year">Year</label>\
                  <input class="form-control" id="due-year" name="year" type="number" pattern="[0-9]*" value="<%=submission.due_at && submission.due_at[1] %>">\
                </div>\
                <div class="icon-calendar datepicker-trigger pull-left"></div>\
                <input type="text" class="datepicker" data-attach="DatePicker" style="width:0;height:0;border:none;outline:none;" value="<%=submission.due_at && submission.due_at[2]%>/<%=submission.due_at && submission.due_at[3]%>/<%= submission.due_at && submission.due_at[1]%>"/>\
              </div>\
            </fieldset>\
          </div>\
        </form>\
        <div class="button-set">\
            <button class="button button-blue" type="button" value="btn-save">Save</button>\
            <button class="button button-grey pull-right dlg-close" type="button">Cancel</button>\
        </div>\
    '
  );

  function constructor(el) {
    var self = this;
    this.el = el;
    this.submission_id = el.attr("data-submissionid");
    this.case_id = el.attr("data-caseid");
    var dueDateStr = el.attr("data-value");
    var dueDate = /^(\d{4})-(\d{1,2})-(\d{1,2})T/.exec(dueDateStr);
    require(["modules/Lightbox"], function (Lightbox) {
      var content = tpForm({ submission: { due_at: dueDate } });
      var lb = new Lightbox({
        content: content,
      });
      var dateEl = lb.getContainer().find(".datepicker");
      if (dateEl.length) {
        require(["jqui/widgets/datepicker"], function (datepicker) {
          dateEl.datepicker();
          lb.getContainer()
            .find(".datepicker-trigger")
            .on("click", function () {
              dateEl.focus();
            });
          dateEl.on("change", function (evt) {
            var dateSplit = /(\d{2})\/(\d{2})\/(\d{4})/.exec(dateEl.val());
            var container = lb.getContainer();
            container.find("[name=day]").val(dateSplit[2]);
            container.find("[name=month]").val(dateSplit[1]);
            container.find("[name=year]").val(dateSplit[3]);
          });
        });
      }

      lb.getContainer()
        .find("button")
        .on("click", function (evt) {
          if ($(evt.target).val() == "btn-save") {
            var container = lb.getContainer();
            var result = helpers.unMap(container.find("form").serializeArray());
            if (!result.year && !result.month && !result.day) {
              var due_at = "";
              var outStr = "n/a";
            } else if (
              Date.parse(
                result.year +
                  "-" +
                  result.month +
                  "-" +
                  result.day +
                  "T00:00:00.000Z"
              ) < Date.now()
            ) {
              alert(
                "You have entered a date that is in the past - Please correct"
              );
            } else {
              var ticks = Date.parse(
                result.year +
                  "-" +
                  result.month +
                  "-" +
                  result.day +
                  "T00:00:00.000Z"
              );
              if (isNaN(ticks)) {
                popups.error("Invalid date");
              } else {
                var dueDate = new Date(ticks);
                var due_at = dueDate.toISOString();
                var outStr = dueDate.format("dd mon yyyy");
              }
            }
            if (!_.isUndefined(due_at)) {
              if (due_at != dueDateStr) {
                $.ajax({
                  url:
                    "/case/" +
                    self.case_id +
                    "/submission/" +
                    self.submission_id +
                    "/",
                  method: "post",
                  dataType: "json",
                  data: {
                    due_at: due_at,
                    csrfmiddlewaretoken: window.dit.csrfToken,
                  },
                }).then(
                  function (result) {
                    lb.close();
                    if (result && result.submission) {
                      if (result.submission.due_at) {
                        var due_date = Date.parseIso(result.submission.due_at);
                      }
                      self.el.html(
                        due_date ? due_date.format("dd mon yyyy") : "n/a"
                      );
                      self.el.attr("data-value", result.submission.due_at);
                    } else {
                      popups.error("Save failed");
                    }
                  },
                  function (result) {
                    popups.error("Save failed");
                  }
                );
              } else {
                lb.close(); // Nothing changed - nothing to do
              }
            }
          }
        });
    });
  }

  return constructor;
});
