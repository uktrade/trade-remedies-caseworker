// widget to upload a file
define(function () {
  "use strict";
  var constructor = function (el) {
    var self = this;
    this.el = el;
    el.on("change", function (evt) {
      onChange.call(self, evt);
    });
    el.on("click", function (evt) {
      trigger.call(self, evt);
    });
    this.container = el.closest(".form-group");
    this.container.on("click", _.bind(onClick, this));
    this.dragTarget = this.container.find(".upload-target");
    this.dragTarget.on("dragover", _.bind(onDragOver, this));
    this.dragTarget.on("dragend", _.bind(endDrag, this));
    this.bodyDragOver = _.bind(bodyDragOver, this);
    this.onDrop = _.bind(onDrop, this);
    buildFileTable.call(this);
  };

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
    return {
      csrfmiddlewaretoken: window.dit.csrfToken,
    };
  }
  function buildFileTable() {
    var self = this;
    this.fileTable = this.fileTable || this.container.find("table.file-list");
    var templateSrc =
      '<tr><td><span class="filename"><a href="/case/<%=data.submission && data.submission.case && data.submission.case.id%>/submission/<%=data.submission && data.submission.id%>/file/<%=data.id%>"><%=name%></a></span></td>\
            <td><span class="nobreak"><%data.size%></nobreak></td>\
            <td><span class="nobreak"><%data.created_at%></nobreak></td>\
            <td>{% if status != "complete" %}<a href="/file?id={{ file.id }}" class="file-delete" data-fileid="{{ file.id }}">Remove</a>{% endif %}</td></tr>';
    this.lineTemplate =
      this.lineTemplate || _.template(templateSrc, { variable: "data" });
    //this.lineTemplate = this.lineTemplate || _.template(this.container.find('table tr.template-line')[0].outerHTML,{'variable':'data'});
    // build a list of files from the table
    this.files = {};
    this.fileTable.find("tbody tr").each(function () {
      var row = $(this);
      var meta = { name: "", id: "", size: "" };
      _.each(meta, function (val, key) {
        meta[key] = row.attr(
          "data-file" + String(key.substr(0, 1)).toUpperCase() + key.substr(1)
        );
      });
      meta["row"] = row;
      self.files[meta.name] = meta;
    });
  }

  // Click on a delete icon
  function onClick(evt) {
    var self = this;
    var aTag = $(evt.target).closest("a.file-delete");
    var fileId = aTag.attr("data-id");
    var submissionId = aTag.attr("data-submissionid");
    var caseId = aTag.attr("data-caseid");
    if (fileId) {
      evt.preventDefault();
      var details = getDetails.call(this);
      details.fileId = fileId;
      details.action = "delete";
      var data = [];
      _.each(details, function (value, key) {
        data.push({ name: key, value: value });
      });
      $.ajax({
        url:
          "/cases/" +
          caseId +
          "/submission/" +
          submissionId +
          "/remove/document/" +
          fileId +
          "/",
        type: "POST",
        data: data,
      }).then(function (result) {
        aTag.closest("tr").remove();
        buildFileTable.call(self);
      });
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

  function addLine(file) {
    // add a new line to the file table
    this.fileTable.removeClass("hidden"); // if this is the first file, the table is pre-hidden
    var row = (this.files[file.name] = { name: file.name, size: file.size });
    var html = this.lineTemplate(file);
    _.each(this.files[file.name], function (val, key) {
      html = html.replace(new RegExp("{" + key + "}", "g"), val);
    });
    var el = (row.row = $(html));
    el.removeClass("hidden");
    this.fileTable.append(el);
    return row;
  }

  function uploadFile(details, file) {
    var self = this;
    var form = $("<form></form>");
    var row = addLine.call(this, file);
    // var row = this.files[file.name] || addLine.call(this,file);
    var progress = $(
      '<td colspan=3><div class="progress-bar"><div></div></div></td>'
    );
    $(row.row).find("td").addClass("hidden");
    $(row.row).find("td").first().removeClass("hidden").after(progress);

    _.each(details, function (value, key) {
      form.append(
        $('<input type="hidden" name="' + key + '" value="' + value + '">')
      );
    });
    var formData = new FormData(form[0]);
    formData.append("file", file);
    try {
      $.ajax({
        url: "/document/create/",
        type: "POST",
        data: formData,
        cache: false,
        contentType: false,
        processData: false,
        xhr: function () {
          var myXhr = $.ajaxSettings.xhr();
          if (myXhr.upload) {
            // For handling the progress of the upload
            myXhr.upload.addEventListener(
              "progress",
              function (e) {
                if (e.lengthComputable) {
                  var pc = Math.floor((e.loaded / e.total) * 100);
                  progress.find("div div").css({ width: pc + "%" });
                }
              },
              false
            );
          }
          return myXhr;
        },
      }).then(
        function (result) {
          var content = self.lineTemplate(result);
          row.row.after($(content));
          row.row.remove();
          progress.remove();
        },
        function (error, type) {
          debugger;
        }
      );
    } catch (e) {
      console.error(e);
    }
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

  function onChange(evt) {
    var self = this;
    var details = getDetails.call(this);

    var data = new FormData(this.form[0]);
    data.forEach(function (file, key) {
      uploadFile.call(self, details, file);
    });
  }
  return constructor;
});
