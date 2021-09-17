// widget to upload a file
define([], function () {
  "use strict";
  var constructor = function (el) {
    var self = this;
    this.el = el;
    this.el.find("button.btn-file-upload").on("click", function (evt) {
      trigger.call(self, evt);
    });
    this.submission_document_type = this.el.attr(
      "data-submission_document_type"
    );
    this.tabSet = this.el.find(".tabset").click(_.bind(clickTab, this));
    this.el.on("click", _.bind(onClick, this));
    this.el.on("change", _.bind(onFormChange, this));
    this.dragTarget = this.el.find(".upload-target");
    this.dragTarget.on("dragover", _.bind(onDragOver, this));
    this.dragTarget.on("dragend", _.bind(endDrag, this));
    this.bodyDragOver = _.bind(bodyDragOver, this);
    this.onDrop = _.bind(onDrop, this);
    this.fileTable = this.el.find("table.file-list");
    buildFileTable.call(this);
    constructTypeahead.call(this);
    this.lineTemplate = _.template(templateSrc, { variable: "document" });
    this.el
      .find("input.test-file")
      .on("change", _.bind(onTestFileChange, this));
  };

  var templateSrc =
    '<tr data-fileid="<%=document.id%>" data-filename="<%=document.name%>" data-filesize="<%=document.size%>">\
        <td><span class="filename"><%=document.name%></span></td>\
        <td><span class="file-size"><%=document.size %></span></td>\
        <td><span class="file-date"><%= document.date %></span></td>\
        <td><% if(document.reference) { %>\
            <% print(document.confidential ? "Confidential" : "Non-confidential") } else {%>\
            <select name="confidential">\
            <option  value="conf" <% if(document.confidential) { %>selected="selected"<% } %> >Confidential</option>\
            <option  value="non-conf" <% if(!document.confidential) { %>selected="selected"<% } %>>Non-confidential</option>\
        </select><% } %></td>\
        <td><a href="javascript:void(0)" class="file-delete link"><i class="icon icon-bin"></i></a></td>\
        </tr>';

  function getBrowseList() {
    var self = this;
    return new Promise(function (resolve, reject) {
      var url = self.el.attr("data-list-url");
      $.ajax({
        url: url,
        cache: false,
        contentType: false,
        processData: true,
      }).then(function (result) {
        var out = [];
        _.each(result, function (file) {
          if (!file.confidential) {
            out.push({
              value: file.name,
              id: file.id,
              size: file.size,
              lastModified: file.created_at,
              confidential: file.confidential,
            });
          }
        });
        resolve(out);
      });
    });
  }

  function constructTypeahead() {
    var self = this;
    self.typeaheadEl = self.el.find("#file-typeahead");
    self.browseList = getBrowseList.call(self).then(function (list) {
      require(["jqui/widgets/autocomplete"], function (autocomplete) {
        self.typeaheadEl.autocomplete({
          source: list,
          select: _.bind(select, self),
          appendTo: ".file_browser .tab_search",
          autofocus: true,
        });
      });
    });
  }

  function select(event, ui) {
    event.preventDefault();
    addLine.call(
      this,
      {
        name: ui.item.value,
        id: ui.item.id,
        lastModified: ui.item.lastModified,
        size: ui.item.size,
        confidential: ui.item.confidential,
      },
      true
    );
  }

  function trigger(evt) {
    var self = this;
    this.form = $(
      '<form><input type="file" name="file" multiple="multiple"></form>'
    );
    this.form
      .find("input")
      .trigger("click")
      .on("change", function (evt) {
        onChange.call(self, evt);
      });
  }

  function buildFileTable() {
    var self = this;
    // build a list of files from the table
    this.fileTable.find("tbody tr").each(function () {
      var row = $(this);
      var data = { name: "", id: "", size: "", confidential: "" };
      _.each(data, function (val, key) {
        data[key] = row.attr(
          "data-file" + String(key.substr(0, 1)).toUpperCase() + key.substr(1)
        );
      });
      this.data = data;
    });
  }

  function clickTab(evt) {
    var selClass = "selected";
    var tab = $(evt.target).closest("a");
    var tabKey = tab.attr("data-tab");
    if (tabKey) {
      this.el.find(".inner").addClass("hidden");
      this.tabSet.find("." + selClass).removeClass(selClass);
      this.el.find("." + tabKey).removeClass("hidden");
      tab.addClass(selClass);
    }
  }

  // Click on a delete icon
  function onClick(evt) {
    var self = this;
    var aTag = $(evt.target).closest("a.file-delete");
    var data = ($(evt.target).closest("tr")[0] || {})["data"];
    if (aTag.length) {
      confirmPopup("Remove document?").then(function () {
        if (data.local) {
          // If it's a local file or reference, it's not actually been saved yet - so simply remove
          evt.preventDefault();
          aTag.closest("tr").remove();
          if (!_.keys(self.fileObjects).length) {
            self.fileTable.addClass("empty");
          }
        } else {
          var subst = {
            caseId: aTag.attr("data-caseId"),
            documentId: aTag.attr("data-id"),
            organisationId: aTag.attr("data-organisationId"),
            submissionId: aTag.attr("data-submissionId"),
          };
          var url = _.template(
            "/case/<%=caseId%>/submission/<%=submissionId%>/document/<%=documentId%>/"
          )(subst);
          $.ajax({
            url: url,
            method: "delete",
            beforeSend: function (xhr) {
              xhr.setRequestHeader("X-CSRFToken", window.dit.csrfToken);
            },
          }).then(
            function (result) {
              aTag.closest("tr").remove();
            },
            function () {
              alert("Failed to delete file");
            }
          );
        }
      });
    }
  }
  function onFormChange(evt) {
    var self = this;
    var data = ($(evt.target).closest("tr")[0] || {})["data"];
    var control = $(evt.target).closest("select[name=confidential]");
    if (control.length) {
      var conf = control.val();
      data.confidential = control.val() == "conf";
    }
  }

  function bodyDragOver(evt) {
    var target = $(evt.target);
    var over = target.closest(".drag-over")[0] === this.dragTarget[0];
    if (!over) {
      endDrag.call(this);
    }
  }

  function startDrag() {
    this.dragging = true;
    this.dragTarget.addClass("drag-over");
    $(document.body).on("dragover", this.bodyDragOver);
    this.dragTarget.on("drop", this.onDrop);
  }

  function endDrag() {
    this.dragging = false;
    this.dragTarget.removeClass("drag-over");
    $(document.body).off("dragover", this.bodyDragOver);
    this.dragTarget.off("drop", this.onDrop);
  }

  function onDragOver(evt) {
    if (!this.dragging) {
      startDrag.call(this);
    }
    evt.preventDefault();
    return true;
  }

  function addLine(file, reference) {
    // add a new line to the file table
    this.fileTable.removeClass("empty"); // if this is the first file, the table is pre-hidden
    var data = {
      local: true,
      file: file,
      name: file.name,
      size: formatBytes(file.size, 1),
      date: formatDateTime(file.lastModified),
      confidential: reference ? file.confidential : true, // by default
      submission_document_type: this.submission_document_type || null,
      reference: reference,
    };
    var el = $(this.lineTemplate(data));
    this.fileTable.append(el);
    el[0].data = data;
  }

  function uploadFile(file) {
    var self = this;
    addLine.call(this, file);
  }

  function onDrop(evt) {
    var self = this;
    endDrag.call(this);
    evt.preventDefault();
    // construct a post for each file
    var files = evt.originalEvent.dataTransfer.files;
    for (var i = 0; i < files.length; i++) {
      uploadFile.call(self, files[i]);
    }
  }

  function onTestFileChange(evt) {
    var self = this;
    var fileInput = $(evt.target);
    this.form = $("<form></form>");
    var parent = fileInput.parent();
    this.form.append(fileInput);
    onChange.call(this);
    parent.append(fileInput);
  }

  function onChange(evt) {
    var self = this;
    var data = new FormData(this.form[0]);
    data.forEach(function (file, key) {
      uploadFile.call(self, file);
    });
  }

  function formatBytes(bytes, decimals) {
    if (bytes == 0) return "0 Bytes";
    var k = 1024,
      dm = decimals <= 0 ? 0 : decimals || 2,
      sizes = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"],
      i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
  }

  function formatDateTime(date) {
    var date = new Date(date);
    var day = date.getDate();
    var month = date.getMonthName();
    var year = date.getFullYear();
    var time =
      date.getHours().toString().pad(2) +
      ":" +
      date.getMinutes().toString().pad(2);

    return day + " " + month + " " + year + " " + time;
  }

  return constructor;
});
