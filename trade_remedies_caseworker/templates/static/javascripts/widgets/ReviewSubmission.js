// widget to upload a file
define(["modules/helpers", "modules/popUps", "modules/logging"], function (
  helpers,
  popups,
  logging
) {
  "use strict";
  const logger = logging.getLogger("reviewsubmission");
  var constructor = function (el) {
    var self = this;
    logger.log("constructor");
    this.outer = el;
    try {
      this.submission = JSON.parse(this.outer.attr("data-submission"));
      logger.log(this.submission);
    } catch (e) {
      console.error(e);
      alert("Bad JSON");
    }
    this.outer.on("change", _.bind(onChange, self));
    this.outer.on("click", _.bind(onClick, self));
    prepareList.call(this);
  };

  function setStatus(status, data) {
    var self = this;
    data = _.extend(
      {
        csrfmiddlewaretoken: window.dit.csrfToken,
        "btn-value": status,
      },
      data
    );
    return new Promise(function (resolve, reject) {
      var parameters = {
        url:
          "/case/" +
          self.submission.case.id +
          "/submission/" +
          self.submission.id +
          "/",
        method: "post",
        dataType: "json",
        data: data,
      };
      $.ajax(parameters).then(function (result) {
        resolve(result);
      }, reject);
    });
  }

  function setReview(status) {
    var self = this;
    return new Promise(function (resolve, reject) {
      $.ajax({
        url:
          "/case/" +
          self.submission.case.id +
          "/submission/" +
          self.submission.id +
          "/",
        method: "post",
        dataType: "json",
        data: {
          csrfmiddlewaretoken: window.dit.csrfToken,
          deficiency_notice_params_review_result: status,
        },
      }).then(function (result) {
        resolve(result);
      }, reject);
    });
  }

  function setParameter(parameter, value) {
    var self = this;
    var form = self.outer.closest("form");
    var data = {
      csrfmiddlewaretoken: window.dit.csrfToken,
    };
    data["deficiency_notice_params_" + parameter] = value;

    return new Promise(function (resolve, reject) {
      $.ajax({
        url: form.attr("action"),
        method: "post",
        dataType: "json",
        data: data,
      }).then(function (result) {
        resolve(result);
      }, reject);
    });
  }

  function setDocumentsDeficiency() {
    var self = this;
    var doc_state = {};
    _.each(this.sliderList, function (val, id) {
      doc_state[id] = { no: "deficient", yes: "sufficient" }[val];
    });
    return $.ajax({
      url:
        "/case/" +
        self.submission.case.id +
        "/submission/" +
        self.submission.id +
        "/documents/",
      method: "post",
      dataType: "json",
      data: {
        csrfmiddlewaretoken: window.dit.csrfToken,
        document_list: JSON.stringify(doc_state),
      },
    });
  }

  function prepareList() {
    var self = this;
    logger.log("prepareList");
    self.sliderList = {};
    self.reviewsLeft = 0;
    self.outer.find(".slider input").each(function () {
      var el = $(this);
      var name = el.attr("name");
      if (_.isUndefined(self.sliderList[name])) {
        self.sliderList[name] = null;
        self.reviewsLeft++;
      }
      if (el.prop("checked")) {
        self.sliderList[el.attr("name")] = el.val();
        self.reviewsLeft--;
      }
    });

    logger.log(`${self.reviewsLeft} reviews left`);

    if (self.reviewsLeft == 0) {
      reviewComplete.call(this);
    }
  }

  function reviewComplete() {
    var sufficient = true;
    var deficient = false;
    _.each(this.sliderList, function (val, docId) {
      deficient = deficient || val == "no";
      sufficient = sufficient && val == "yes";
    });
    this.outer
      .setClass("sufficient", sufficient)
      .setClass("deficient", deficient);
  }

  function onChange(evt) {
    var target = $(evt.target);

    if (target.closest(".slider").length && target.prop("checked")) {
      var docId = target.attr("name");
      if (!this.sliderList[docId]) {
        this.reviewsLeft--;
      }
      this.sliderList[docId] = target.val();
      if (this.reviewsLeft <= 0) {
        reviewComplete.call(this);
      }
    }
  }

  function error(res) {
    console.error(res);
    alert("Save failed");
  }

  function onClick(evt) {
    var self = this;
    var value = $(evt.target).val();
    var statusValue = "sufficient";
    if (value in { reject: 1, approve: 1, save: 1 }) {
      setDocumentsDeficiency.call(this).then(function () {
        switch (value) {
          case "reject":
            statusValue = "deficient";
            setReview.call(self, "deficient").then(function () {
              window.location.reload();
            }, error);
            break;
          case "approve":
            setStatus.call(self, "sufficient").then(function (result) {
              if (result && result.alert) {
                location.assign("?alert=" + result.alert);
              } else {
                window.location.reload();
              }
            }, error);
            break;
        }
      }, error);
    }
    if (value in { "publish-start": 1, "publish-cancel": 1 }) {
      setParameter
        .call(self, "publish", value == "publish-start")
        .then(function () {
          window.location.reload();
        });
    }

    if (value in { withdraw: 1 }) {
      popups
        .confirm(
          "Are you sure you want to withdraw this submission from the public file?"
        )
        .then(function () {
          setStatus.call(self, "withdraw").then(function (result) {
            setParameter.call(self, "publish", "__remove").then(function () {
              if (result.redirect_url) {
                window.location.assign(result.redirect_url);
              } else {
                window.location.reload();
              }
            });
          });
        });
    }
  }

  return constructor;
});
