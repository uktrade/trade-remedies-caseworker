define([], function () {
  "use strict";

  var sliderTemplate = _.template(`
        <div class="slider <%=value%>" data-attach="slider" >
            <label><span tabindex="0">Yes</span><input type="radio" name="<%=name%>" value="yes" <% if(value == 'yes') print('checked="checked"'); %>></label>
            <label><span tabindex="0">No</span><input type="radio" name="<%=name%>" value="no" <% if(value == 'no') print('checked="checked"'); %>></label>
        </div>
        `);

  var checkboxTemplate = _.template(`
            <div class="multiple-choice small">
                <label>
                <span class="form-label">
                    Link to this page?
                </span>
                <input class="pull-left" type="checkbox" checked="true">
                <label></label>
                </label>
            </div>
        `);

  var constructor = function (el) {
    this.el = el;
    this.viewMode = el.attr("data-mode") == "view";
    _.bindAll(this, "selectorChange");
    this.$caseId = this.el.find("[name=case_id]") || dit.case_id;
    this.$contentType = this.el.find("[name=content_type]") || dit.content_type;
    this.$modelId = this.el.find("[name=model_id]") || dit.model_id;
    this.$modelKey = this.el.find("[name=model_key]");
    this.link = $('<a class="button-link"></a>');
    this.selector = $(checkboxTemplate({ name: "link_to_page", value: "yes" }));
    this.selector.on("change", _.bind(this.selectorChange, this));
    this.$fields = $("<div></div>");
    this.el
      .append(this.link)
      .append(this.selector)
      .append(this.$fields)
      .attachWidgets();
    this.refresh();
    this.selectorChange();
  };

  var jumpTable = {
    submission: {
      urlTemplate: "/case/<%=caseId%>/submission/<%=modelId%>/",
      label: "Jump to linked submission",
      linkLabel: "Link task to this submission",
      contentType: "cases.submission",
    },
    organisation: {
      urlTemplate: "/case/<%=caseId%>/organisation/<%=modelId%>/",
      label: "Jump to linked organisation",
      linkLabel: "Link task to this organisation",
      contentType: "organisations.organisation",
    },
    "case workflow": {
      urlTemplate: "/case/<%=caseId%>/actions/#<%=modelKey%>",
      label: "Jump to linked workflow",
      linkLabel: "Link task to this workflow page",
      contentType: "cases.caseworkflow",
    },
    parties: {
      urlTemplate: "/case/<%=caseId%>/parties/",
      label: "Jump to the parties page",
    },
    submissions: {
      urlTemplate: "/case/<%=caseId%>/submissions/",
      label: "Jump to the submissions page",
    },
    case_page: {
      urlTemplate: "/case/<%=caseId%>/",
      label: "Jump to the case homepage",
    },
    content: {
      urlTemplate: "/case/<%=caseId%>/section/<%=modelKey%>/",
      label: "Jump to the linked note",
      linkLabel: "Link task to this note page",
      contentType: "content.content",
    },
  };

  constructor.prototype = {
    getPageParameters: function () {
      var settings = {};
      if (dit.submission_id) {
        settings.model_id = dit.submission_id;
        settings.content_type = "cases.submission";
      } else if (dit.organisation_id) {
        settings.model_id = dit.organisation_id;
        settings.content_type = "organisations.organisation";
      }
      if (dit.page == "actions") {
        var state = JSON.parse($("#state-json").val()) || {};
        settings.model_id = state.id;
        settings.content_type = "cases.caseworkflow";
        settings.model_key = (location.hash || "").replace("#", "");
      }
      if (dit.page in { parties: 1, submissions: 1, case_page: 1 }) {
        settings.model_key = dit.page;
      }
      if (dit.content_type) {
        settings.content_type = dit.content_type;
        settings.model_id = dit.model_id;
        settings.model_key = dit.model_key;
      }
      if (_.keys(settings).length) {
        return settings;
      }
    },

    selectorChange: function () {
      var self = this;
      var selected = this.selector.find("input[type=checkbox]:checked").length;
      self.$fields.html("");
      if (selected) {
        _.each(this.getPageParameters(), function (value, key) {
          self.$fields.append(
            $(`<input type="hidden" name="${key}" value="${value}">`)
          );
        });
      }
    },

    refresh: function () {
      var contentType = this.$contentType.val();
      var modelId = this.$modelId.val();
      var modelKey = this.$modelKey.val();
      var jump = jumpTable[contentType || modelKey];
      var pageParams = this.getPageParameters();
      if (jump) {
        this.link.removeAttr("disabled", 1);
        this.link.attr(
          "href",
          _.template(jump.urlTemplate)({
            caseId: this.$caseId.val() || window.dit.caseId,
            modelId: this.$modelId.val(),
            modelKey: modelKey,
          })
        );
        this.link.text(jump.label);
        // are we on the linked page already?
        if (
          pageParams &&
          pageParams.content_type == jump.contentType &&
          (pageParams.model_id || "") == modelId &&
          (pageParams.model_key || "") == modelKey
        ) {
          // we are!
          this.link.attr("disabled", 1);
          this.link.text("This task is linked to the page you are on");
        }
        this.link.show();
        this.selector.setClass("js-hidden", true);
      } else {
        this.link.hide();
        if (!this.viewMode && pageParams) {
          var labelText = "Link to this page?";
          if (pageParams.content_type) {
            _.each(jumpTable, function (val, key) {
              if (val.contentType == pageParams.content_type) {
                labelText = val.linkLabel;
              }
            });
          }
          this.selector.find("span.form-label").text(labelText);
        }
        this.selector.setClass("js-hidden", !pageParams || this.viewMode);
      }
    },
  };

  return constructor;
});
