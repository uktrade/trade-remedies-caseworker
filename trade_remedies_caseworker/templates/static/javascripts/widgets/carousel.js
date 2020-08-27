/*
Drives a carousel on click of the drive blobs
*/
define(["modules/helpers", "modules/popUps", "modules/Events"], function (
  helpers,
  popups,
  Events
) {
  "use strict";

  function constructor(el) {
    this.outer = el.closest(".carousel-surround");
    this.outer.on("click", _.bind(onClick, this));
    var twoCells = this.outer.find(".carousel-table > .row > .cell");
    this.primary = $(twoCells[0]).find(".party-card-inner");
    this.mergeList = $(twoCells[1]).find(".party-card-inner");
    if (this.mergeList.length == 0) {
      this.mergeList = this.primary;
    }
    this.blobs = this.outer.find("a.blob");
    this.length = this.blobs.length;
    this.nextButton = this.outer.find(".carousel-button.next");
    this.previousButton = this.outer.find(".carousel-button.previous");
    this.selected = 0;
    el.on("mouseover", _.bind(onMouseOver, this));
    this.selectItem(0);
  }

  function onClick(evt) {
    var self = this;
    var blob = $(evt.target);
    if (blob.is("a.blob")) {
      this.selectItem(blob.attr("data-item") - 1);
    }
    if (blob.is(".carousel-button")) {
      this.selectItem(this.selected - 0 + (blob.hasClass("previous") ? -1 : 1));
    }
    if (blob.is("button") && blob.val() in { merge: 1, "undo-nomerge": 1 }) {
      // find selected party
      var outerCells = this.outer.find(".carousel-table >.row > .cell");
      var mainParty = $(outerCells[0])
        .find(".party-card-inner")
        .attr("data-party-id");
      var party2Container = $(outerCells[1]).find(".party-card-inner")[
        this.selected
      ];
      var party2 = $(party2Container).attr("data-party-id");
      if (blob.val() == "merge") {
        this.openMergeBox(mainParty, party2);
      } else {
        this.undoNoMerge(mainParty, party2);
      }
    }
  }

  function onMouseOver(evt) {
    var target = $(evt.target);
    if (target.hasClass("auto-expand") && this.lastTarget != evt.target) {
      this.lastTarget = evt.target;
      if (evt.target.scrollWidth != target.width() && !target.attr("title")) {
        $(this.lastTarget).attr("title", $(this.lastTarget).text().trim());
      }
    }
  }

  var rowTemplate = _.template(
    '<div class="row">\
      <div class="cell"><span class="bold"><%=label%></span></div>\
      <div class="cell with-radio">\
        <div class="big-radio pull-left">\
          <input type="radio" id="<%=field%>-1" name="<%=field%>" value="p1" <% if(!select2) print("checked"); %> >\
          <label for="<%=field%>-1"></label>\
        </div>\
        <%=(value1 || \'&lt;empty&gt;\') %>\
      </div>\
      <div class="cell with-radio">\
        <div class="big-radio pull-left">\
          <input type="radio" id="<%=field%>-2" name="<%=field%>" value="p2" <% if(select2) print("checked"); %> >\
          <label for="<%=field%>-2"></label>\
        </div>\
        <%=(value2 || \'&lt;empty&gt;\') %>\
      </div>\
    </div>'
  );

  constructor.prototype = {
    selectItem: function (item) {
      if (item >= this.length) item = this.length - 1;
      if (item < 0) item = 0;
      this.selected = item;
      this.previousButton[item <= 0 ? "hide" : "show"]();
      this.nextButton[item >= this.length - 1 ? "hide" : "show"]();

      this.updateTicks();
      var margin = (item - 0) * -100 + "%";
      (this.slider = this.slider || this.outer.find(".carousel-slider")).css({
        marginLeft: margin,
      });
      this.blobs.siblings().removeClass("active");
      $(this.blobs[item]).addClass("active");
      // enable/disable merge
      this.lowerControls =
        this.lowerControls || this.outer.find(".lower-controls");
      var disableJson = $(this.mergeList[item])
        .closest(".cell")
        .find(".disable-params")
        .val();
      if (disableJson) {
        var disableData = JSON.parse(disableJson) || {};
        this.lowerControls
          .find(".at")
          .text(Date.parseIso(disableData.at).format("dd mon yyyy"));
        this.lowerControls.find(".by").text(disableData.by);
      }
      this.lowerControls
        .find(".merge-denied-message")
        [!disableData ? "addClass" : "removeClass"]("js-hidden");
      this.lowerControls
        .find(".merge-button")
        [!!disableData ? "addClass" : "removeClass"]("js-hidden");
    },
    updateTicks: function () {
      this.selectedCard = $(this.mergeList[this.selected]);
      var secondaryRows = this.selectedCard.find(".row, .name-row");
      this.primary.find(".row, .name-row").each(function (index) {
        //$(this).setClass('equal', $(secondaryRows[index]).hasClass('match'));
        var val1 = $(secondaryRows[index]).attr("data-value");
        var val2 = $(this).attr("data-value");
        var notequal = val1 && val2 && val1 != val2;
        $(this).setClass("equal", notequal);
        $(secondaryRows[index]).setClass("equal", notequal);
      });
    },
    getMergeQuestions: function () {
      this.selectedCard = $(this.mergeList[this.selected]);
      var secondaryRows = this.selectedCard.find(".row, .name-row");
      var out = "";
      this.primary.find(".row, .name-row").each(function (index) {
        var secondaryRow = $(secondaryRows[index]);
        var field = $(this).attr("data-field");
        var value1 = $(this).attr("data-value");
        var value2 = secondaryRow.attr("data-value");
        //if(field && (value1 || value2) && (value1 != value2)) { // to only show fields with different values
        if (field) {
          out += rowTemplate({
            label: $(this).find(".label").text(),
            field: field,
            value1: value1,
            value2: value2,
            select2: value2 && !value1,
          });
        }
      });
      if (out) {
        return `
            <div class="info">Some fields have different values. Please select which value to pick</div>
            <form><div class="table align-top merge-selection">${out}</div>
            <div class="column-two-thirds margin-left-1">
              <div class="multiple-choice">
                <input id="merge_confirm" type="radio" value="merge" name="merge_confirm">
                <label for="{{ task.key }}">All required checks are completed and I can now complete the merge of these organisations.</label>
              </div>
              <div class="multiple-choice">
                <input id="merge_confirm" type="radio" value="no_merge" name="merge_confirm">
                <label for="{{ task.key }}">All required checks are completed and these organisations should not be merged.</label>
              </div>
            </div>
            <div class="button-container pull-left margoin-top-1">
              <button type="button" value="merge" class="button button-blue dlg-close">Save and exit</button>
              <button type="button" value="" class="button button-grey dlg-close pull-right">Cancel</button>
            </div>
            </form>
            `;
      }
      return "Are you sure you want to merge these organisations?";
    },
    openMergeBox: function (party1Id, party2Id) {
      var self = this;
      require(["modules/Lightbox"], function (Lightbox) {
        self.dlg = new Lightbox({
          title: "Confirm Merge",
          message: self.getMergeQuestions(),
          buttons: {},
        });
        var btnMerge = self.dlg.getContainer().find("button[value=merge]");
        btnMerge.on("click", function () {
          var data = helpers.unMap(
            self.dlg.getContainer().find("form").serializeArray()
          );
          switch (data.merge_confirm) {
            case "merge":
              popups
                .confirm(
                  'Are you sure you want to merge these organisations?<br><span class="bold">Warning:</span> this action cannot be reversed.',
                  "Merge now"
                )
                .then(function () {
                  self.merge(party1Id, party2Id, data);
                });
              break;
            case "no_merge":
              popups
                .confirm(
                  "Are you sure you want to mark these organisations as 'not to be merged'?",
                  "Never merge"
                )
                .then(function () {
                  self.no_merge(party1Id, party2Id);
                });
          }
        });
      });
    },
    updateJson: function (party, json) {
      var json_text = this.primary.find("textarea.json-data").val() || "{}";
      var json_data = JSON.parse(json_text) || {};
      helpers.deepExtend(json_data, json);
      return $.ajax({
        method: "post",
        dataType: "json",
        url: "/organisation/" + party + "/edit/",
        data: {
          json_data: JSON.stringify(json_data),
          csrfmiddlewaretoken: window.dit.csrfToken,
        },
      });
    },
    no_merge: function (party1, party2) {
      var now = new Date().toISOString();
      var user = JSON.parse($("#user_json").val() || "{}");
      var no_merge = {};
      no_merge[party2] = { at: now, by: user.name };
      this.updateJson(party1, { no_merge: no_merge }).then(function (result) {
        popups
          .alert(
            "The organisations have been marked as non-mergeable.",
            "Information"
          )
          .then(function () {
            new Events().fire("party-updated");
          });
      });
    },
    undoNoMerge: function (party1, party2) {
      var self = this;
      popups
        .confirm(
          "Are you sure you want to remove the 'do not merge' flag from these organisations?",
          'Remove "don\'t merge" flag.'
        )
        .then(function () {
          var noMerge = {};
          noMerge[party1] = noMerge[party2] = "(delete)";
          self
            .updateJson(party1, { no_merge: noMerge })
            .then(function (result) {
              self
                .updateJson(party2, { no_merge: noMerge })
                .then(function (result) {
                  popups
                    .alert(
                      'The "do not merge" flag has been removed.',
                      "Information"
                    )
                    .then(function () {
                      new Events().fire("party-updated");
                    });
                });
            });
        });
    },
    merge: function (party1, party2, parameter_map) {
      var data = {
        parameter_map: JSON.stringify(parameter_map),
        merge_with: party2,
        csrfmiddlewaretoken: window.dit.csrfToken,
      };
      $.ajax({
        method: "post",
        dataType: "json",
        url: "/organisation/" + party1 + "/merge/",
        data: data,
      }).then(function (results) {
        if (results.result.errors) {
          popups.alert(results.result.errors[0], "Error");
        } else {
          popups
            .alert(
              "The organisations have been merged sucessfully",
              "Information"
            )
            .then(function () {
              new Events().fire("party-updated");
            });
        }
      });
    },
  };

  return constructor;
});
