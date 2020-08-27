// widget to upload a file
define(["modules/helpers"], function (helpers) {
  "use strict";

  var constructor = function (el) {
    var self = this;
    this.el = el.find(".file-browser");
    this.submission_document_type = this.el.attr(
      "data-submission_document_type"
    );
    this.form = el.closest("form");
    this.form.on("submit", _.bind(submitForm, this));
    this.el
      .find("button.btn-file-upload")
      .on("click", function (evt) {
        trigger.call(self, evt);
      })
      .removeAttr("disabled");
    //el.on('change',function(evt){onChange.call(self,evt)});
    this.tabSet = this.el.find(".tabset").on("click", _.bind(clickTab, this));
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
      .on("change", _.bind(onTestFileChange, this))
      .removeAttr("disabled");
    this.documentConfidentialLock = this.el.attr(
      "data-document_confidential_lock"
    );
    this.form.find("button[value=save]").removeAttr("disabled"); // indicate to test that we are ready to go
  };

  var templateSrc =
    '<tr data-fileid="<%=document.id%>" data-filename="<%=document.name%>" data-filesize="<%=document.size%>">\
        <td><span class="filename"><%=document.name%></span></td>\
        <td><span class="file-size"><%=document.size %></span></td>\
        <td><span class="file-date"><%= document.date %></span></td>\
        <td>\
            <% if(!document.documentConfidentialLock) { %>\
                <% if(document.reference) { %>\
                <% print(document.confidential ? "Confidential" : "Non-confidential") } else {%>\
                <select name="confidential">\
                    <option  value="conf" <% if(document.confidential) { %>selected="selected"<% } %> >Confidential</option>\
                    <option  value="non-conf" <% if(!document.confidential) { %>selected="selected"<% } %>>Non-confidential</option>\
                </select><% } %>\
            <% } else { %>\
                <input type="hidden" name="confidential" value="<%=document.documentConfidentialLock%>"/>\
            <% } %>\
        </td>\
        <td><a href="javascript:void(0)" class="file-delete link"><i class="icon icon-bin"></i></a></td>\
        </tr>';

  function getBrowseList() {
    var self = this;
    return new Promise(function (resolve, reject) {
      var url = self.el.attr("data-list-url");
      var searchContentType = self.el.attr("data-content_type");
      if (!url) {
        return resolve([]);
      }
      $.ajax({
        url: url,
        cache: false,
        contentType: !searchContentType ? false : searchContentType,
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

  function getDetails() {
    var out = {
      csrfmiddlewaretoken: window.dit.csrfToken,
    };
    var form = this.el.closest("form");
    if (form) {
      var formData = new FormData(form[0]);
      for (var item of formData.entries()) {
        out[item[0]] = item[1];
      }
    }

    return {
      csrfmiddlewaretoken: window.dit.csrfToken,
    };
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

  function notifySubmission(url, alert) {
    $("#modalButton").attr("data-url", url);
    $("#modalButton").attr("data-alert", alert);
    $("#modalButton").click();
  }

  function submitForm(evt) {
    var form = $(evt.target);
    var self = this;
    var notify;
    evt.preventDefault();
    var formData = new FormData(evt.target);
    var button = $(document.activeElement);
    if (button.length) {
      var buttonVal = button.val();
      formData.append(button.prop("name"), button.val());
      notify = button.attr("data-notify");
    }
    this.fileTable.find("tr[data-filename]").each(function () {
      var data = this.data;
      if (data.local) {
        // It's a file that's been added since the last saved
        if (data.file && !data.file.id) {
          // it's a new file to upload
          formData.append("files", data.file);
          formData.append("meta", JSON.stringify(data));
        } else {
          // it's a case file
          formData.append("case_files", "" + data.file.id);
          formData.append("meta", JSON.stringify(data));
        }
        data.local = false; // So we don't try to upload it more than once
      }
    });

    var values = {
      case_id: form.attr("data-case"),
      submission_id: self.submission_id || form.attr("data-submission"),
      //            organisation_id: form.attr('data-organisation'),
      notify_url: self.form.attr("data-notify-url") || "/notify/",
    };
    var action = form.attr("action");
    // var action = _.template( values.submission_id ?
    //     '/case/<%=case_id%>/submission/<%=submission_id%>/':
    //     //'/case/<%=case_id%>/organisation/<%=organisation_id%>/submission/create/')(values)
    //     '/case/<%=case_id%>/submission/create/')(values)
    var default_redirect_url = form.attr("data-redirect");
    try {
      $.ajax({
        url: action,
        type: "POST",
        data: formData,
        cache: false,
        contentType: false,
        processData: false,
      }).then(
        function (result) {
          if (_.isString(result)) {
            try {
              result = JSON.parse(result);
            } catch (e) {
              if (result.substr(1, 10).indexOf("#32;") == -1) {
                // only replace content if it's not a login
                parent = form.parent();
                form.replaceWith($(result).find("form"));
                $(document.body).attachWidgets();
              }
              return;
            }
          }
          self.submission_id = self.submission_id || result.submission_id;
          if (result.errors) {
            var params = helpers.urlParameters();
            params["errors"] = result.errors;
            helpers.urlParameters(params);
            return;
          }
          if (notify) {
            notifySubmission(
              _.template(
                "/case/<%=case_id%>/submission/<%=submission_id%><%=notify_url%>"
              )(values),
              buttonVal
            );
          } else {
            var finalised = result["status"] == "LIVE";
            if (finalised) {
              location.assign("?alert=finalised");
            } else if (result.redirect_url) {
              location.assign(result.redirect_url);
            } else if (default_redirect_url) {
              location.assign(default_redirect_url);
            } else {
              location.reload();
            }
          }
        },
        function (error, type) {
          console.error(error);
          window.alert("Failed to save data");
        }
      );
    } catch (e) {
      console.error(e);
    }
  }

  function clickTab(evt) {
    var selClass = "selected";
    var tab = $(evt.target).closest("li");
    var tabKey = tab.find("a").attr("data-tab");
    if (tabKey) {
      this.el.find(".inner").addClass("hidden");
      this.tabSet.find("." + selClass).removeClass(selClass);
      var page = this.el.find("." + tabKey);
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
          if (!self.fileTable.find("tbody tr:not(.empty-line)").length) {
            self.fileTable.addClass("empty");
          }
        } else {
          var subst = {
            caseId: aTag.attr("data-caseId"),
            documentId: aTag.attr("data-id"),
            organisationId: aTag.attr("data-organisationId"),
            submissionId: aTag.attr("data-submissionId"),
            bundleId: aTag.attr("data-bundleId"),
          };
          if (subst.caseId && subst.submissionId) {
            var url = _.template(
              "/case/<%=caseId%>/submission/<%=submissionId%>/document/<%=documentId%>/"
            )(subst);
          } else {
            var url = _.template(
              "/documents/bundle/<%=bundleId%>/remove/document/<%=documentId%>/"
            )(subst);
          }
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
      reference: reference,
      submission_document_type: this.submission_document_type || null,
      documentConfidentialLock: this.documentConfidentialLock,
    };
    var el = $(this.lineTemplate(data));
    this.fileTable.append(el);
    el[0].data = data;
  }
  /*
    function addFileToForm(file) {
    // don't upload a file, but add it to the form
        var form = this.el.closest('form');

    }
*/
  function uploadFile(details, file) {
    var self = this;
    addLine.call(this, file);
  }

  function onDrop(evt) {
    var self = this;
    endDrag.call(this);
    evt.preventDefault();
    var details = getDetails.call(this);
    // construct a post for each file
    var files = evt.originalEvent.dataTransfer.files;
    for (var i = 0; i < files.length; i++) {
      uploadFile.call(self, details, files[i]);
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
    var details = getDetails.call(this);
    var data = new FormData(this.form[0]);
    data.forEach(function (file, key) {
      uploadFile.call(self, details, file);
    });
  }

  function formatBytes(bytes, decimals) {
    if (bytes == 0) return "0 bytes";
    var k = 1024,
      dm = decimals <= 0 ? 0 : decimals || 2,
      sizes = ["bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"],
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
