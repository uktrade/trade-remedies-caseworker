// widget to upload a file
define(["modules/helpers", "modules/popUps", "modules/Events"], function (
  helpers,
  popups,
  Events
) {
  "use strict";

  var constructor = function (el) {
    this.el = el;
    el.on("click", _.bind(onClick, this));
    this.data = JSON.parse(el.find("#verify-json").val());
    this.tasklist = el.find(".task-list");
    this.editPage = el.find(".edit-page");
    this.editPage.on("submit", _.bind(onSubmit, this));
    new Events().listen("party-updated", _.bind(partyUpdated, this));
  };

  function partyUpdated() {
    if (this.page == "mergeOrganisation") {
      this[this.page]();
    }
  }

  function onClick(evt) {
    var self = this;
    var target = $(evt.target);
    var task = target.attr("data-function");
    if (task) {
      this.page = task;
      (this[task] || _.noop).call(this);
    } else {
      if (target.hasClass("dlg-close")) {
        if (this.url) {
          evt.preventDefault();
          evt.stopPropagation();
          this.tasklist.show();
          this.editPage.hide();
          delete this.url;
        } else {
          if (!isValidated(this.updateData || this.data)) {
            popups
              .alert(
                "Validation of this organisation is not yet complete.<br>All steps must be completed before the organisation is granted acccess to the case.",
                "Warning"
              )
              .then(function () {
                self.refreshOnUpdate();
              });
          } else {
            this.refreshOnUpdate();
          }
        }
      }
    }
  }

  function onSubmit(evt) {
    var self = this;
    evt.preventDefault();
    evt.stopPropagation();
    var form = this.editPage.find("form");
    var data = helpers.unMap(form.serializeArray(true));
    // special confirmations
    if (data["deficiency_notice_params_org_verify"] == "rejected") {
      popups
        .confirm(
          `Marking this organisation as fraudulent is permanent and irreversible<br>
                It will be removed from this case<br>
                No further submissions will be made visible to investigators from this organisation in this or any future cases<br>
                Are you certain that this organisation is fraudulent?`
        )
        .then(function () {
          self.sendData(data);
        });
    } else {
      self.sendData(data);
    }
    return false;
  }

  function isValidated(data) {
    var vals = {
      approved: "submission.organisation_case_role_outer.approved_at",
      notified: "submission.deficiency_notice_params.notification_sent_at",
      validated: "submission.organisation_case_role_outer.approved_at",
      role: "submission.organisation_case_role_outer.role.key",
    };
    _.each(vals, function (val, key) {
      vals[key] = helpers.get(data, val);
    });
    var complete =
      (vals.validated || vals.role == "rejected") &&
      (vals.notified || vals.role == "applicant");
    return complete;
  }

  constructor.prototype = {
    refreshOnUpdate: function () {
      // after a save, refresh the page if something significant changes
      if (this.updateData) {
        if (isValidated(this.updateData) != isValidated(this.data)) {
          window.location.reload();
        }
      }
    },

    reload: function () {
      var self = this;
      delete this.url; // marks that we are no longer in a task
      delete this.page;
      var caseId = this.data.submission.case.id;
      var orgId = this.data.organisation.id;
      var url = `/case/${caseId}/organisation/${orgId}/verify_caserole_tasks/`;
      $.ajax({
        url: url,
        method: "GET",
      }).then(function (result) {
        var tmp = $(result);
        self.updateData = JSON.parse(tmp.find("#verify-json").val());
        var tasklist = tmp.find(".task-list");
        self.tasklist.html(tasklist.html());
        self.tasklist.show();
        self.editPage.hide();
      });
    },
    openPage: function (urlTemplate) {
      var self = this;
      this.url = urlTemplate(this.data);
      $.ajax({
        url: self.url,
      }).then(function (result) {
        // make sure page returned wasn't the login page
        if (result.substr(1, 10).indexOf("#32;") == -1) {
          self.editPage.html(result);
          self.editPage.attachWidgets();
          self.editPage.show();
          self.tasklist.hide();
        }
      });
    },
    sendData: function (data) {
      var self = this;
      return new Promise(function (resolve, reject) {
        _.extend(data, {
          csrfmiddlewaretoken: window.dit.csrfToken,
        });
        $.ajax({
          url: self.url,
          method: "POST",
          data: data,
          dataType: "json",
        }).then(
          function (result) {
            if (result.new_role) {
              if (result.new_role.key == "rejected") {
                popups.alert(
                  `You have rejected ${self.data.organisation.name} from the case.`
                );
              } else {
                popups.alert(
                  `You have approved ${self.data.organisation.name} as a ${result.new_role.name}.<br>Complete the notify step to give them access to the case.`
                );
              }
            }
            self.reload();
            resolve();
          },
          function (err) {
            popups.alert(`Failed to save data (${err.statusText})`, "Error");
          }
        );
      });
    },
    selectLoa: function () {
      this.openPage(
        _.template(
          "/case/<%=submission.case.id%>/organisation/<%=organisation.id%>/loadoc/"
        )
      );
    },
    LoaDetails: function () {
      this.openPage(
        _.template(
          "/case/<%=submission.case.id%>/organisation/<%=organisation.id%>/loa/"
        )
      );
    },
    mergeOrganisation: function () {
      this.openPage(
        _.template(
          "/case/<%=submission.case.id%>/organisation/<%=organisation.id%>/merge_organisation/"
        )
      );
    },
    verifyOrganisation: function () {
      this.openPage(
        _.template(
          "/case/<%=submission.case.id%>/organisation/<%=organisation.id%>/verify_organisation/"
        )
      );
    },
    verifyContactOrganisation: function () {
      this.openPage(
        _.template(
          "/case/<%=submission.case.id%>/organisation/<%=organisation.id%>/verify_organisation/?org_id=<%=submission.contact.user.organisation.organisation.id%>"
        )
      );
    },
    acceptToCase: function () {
      this.openPage(
        _.template(
          "/case/<%=submission.case.id%>/organisation/<%=organisation.id%>/accept/"
        )
      );
    },
    notify: function () {
      this.openPage(
        _.template(
          "/case/<%=submission.case.id%>/organisation/<%=organisation.id%>/notify/"
        )
      );
    },
  };

  return constructor;
});
