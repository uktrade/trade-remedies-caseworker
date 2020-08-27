define(["modules/Events"], function (Events) {
  "use strict";
  var constructor = function (el) {
    this.el = el;
    el.addClass("sortable");
    this.header = this.el.find("th").first().closest("tr");
    this.header.on("click", _.bind(onClick, this));
    this.tbody = this.el.find("tbody").first();
    if (!this.header.find(".sort-indicator").length) {
      this.decorateColumns(this);
    }
    getRows.call(this);
    var activeHeader = this.header.find(".sort-active");
    sortCol.call(this, activeHeader);
    return this;
  };

  constructor.prototype = {
    sortTable: function (colIndex, direction) {
      (this.selectedHeader || this.header.find(".sort-active")).removeClass(
        "sort-active"
      );
      this.selectedHeader = $(this.header.find("th")[colIndex]);
      this.selectedHeader.addClass("sort-active");
      this.selectedHeader.setClass("asc", direction > 0);
      if (!_.isUndefined(colIndex)) {
        this.sortBody(colIndex, direction);
      }
    },
    sortBody: function (colIndex, direction) {
      var self = this;
      new Events().fire("tablesort", {
        colIndex: colIndex,
        direction: direction,
        self: self,
      });
      getRows.call(this);
      self.rows = self.rows.sort(function (rowA, rowB) {
        var ea = rowA.cols[colIndex],
          eb = rowB.cols[colIndex];
        ea.sortval = ea.sortval || $(ea).attr("sortval") || $(ea).text();
        eb.sortval = eb.sortval || $(eb).attr("sortval") || $(eb).text();
        var ca = ea.sortval,
          cb = eb.sortval;
        return (ca > cb ? 1 : ca < cb ? -1 : 0) * direction;
      });
      _.each(self.rows, function (row, idx) {
        self.tbody.prepend(row.tr);
        // $(row.tr).setClass('odd-row', !(idx % 2)); for zebra stripes
      });
    },
    decorateColumns: function () {
      this.header.find("th").each(function () {
        var target = $(this);
        if (!target.hasClass("no-sort")) {
          var sortIndicator = $(
            '<a class="sort-indicator pull-left" href="javascript:void(0)"><span class="visually-hidden">Sort by ' +
              $(this).text() +
              "</span></a>"
          );
          target.append(sortIndicator);
        }
      });
    },
  };

  function onClick(evt) {
    var thisHeader = $(evt.target).closest("th");
    sortCol.call(this, thisHeader);
  }

  function sortCol(sortHeader) {
    var selectedHeaderIndex = this.header.find("th").index(sortHeader);
    if (selectedHeaderIndex >= 0) {
      this.sortTable(selectedHeaderIndex, sortHeader.hasClass("asc") ? -1 : 1);
    }
  }

  function getRows() {
    var rows = (this.rows = []);
    this.el.find("tbody tr").each(function (tr) {
      rows.push({ tr: this, cols: $(this).find("td") });
    });
  }

  return constructor;
});
