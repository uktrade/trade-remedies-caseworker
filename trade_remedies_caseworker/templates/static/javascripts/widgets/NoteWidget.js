// Notelist - add, edit and delete notes
define(["modules/popUps", "modules/moment.min", "modules/helpers"], function (
  popups,
  moment,
  helpers
) {
  "use strict";
  var constructor = function (el) {
    var self = this;
    el.on("click", _.bind(onClick, this));
    //el.on('click',function(evt){trigger.call(self,evt)});

    this.el = el;
    this.defaults = {
      content_type: el.attr("data-content-type"),
      model_id: el.attr("data-model-id"),
      model_key: el.attr("data-model-key"),
      case_id: el.attr("data-case-id") || dit.caseId,
    };
    this.dragTarget = this.el.find(".upload-target");
    this.onDragOver = _.bind(onDragOver, this);
    this.bodyDragOver = _.bind(bodyDragOver, this);
    this.onDrop = _.bind(onDrop, this);
    this.closeDialog = _.bind(closeDialog, this);
    this.compactMode = el.hasClass("compact");
    this.getNote().then(function () {
      if (self.isScanning()) {
        self.pollForNotScanning();
      }
      self.renderWidget();
    });
    var html = tmpNoteWidget({ context: {} });
    this.el.html(html);
  };

  var dlg;

  var dialog = _.template(
    `
        <div class="note-edit">
        <button class="link close-link" value="cancel">&#x2715;</button>
        <form action="/case/<%=(obj.case && obj.case.id) || obj.caseId %>/note/<% if(obj.id) print(obj.id + '/')%>?__prefix=<%=(obj.case && obj.case.id) || obj.caseId %>" method="post">
        <%=obj.csrfToken_input%>
        <input type="hidden" name="note_id" value="<%=obj.id%>">
        <input type="hidden" name="content_type" value="<%=obj.content_type%>">
        <input type="hidden" name="model_id" value="<%=obj.model_id%>">
        <input type="hidden" name="model_key" value="<%=obj.model_key%>">
        <h1 class="heading-medium"><%= obj.title %></h1>
        <div class="edit-upload-block">
            <div class="form-group edit-item type-textArea column-one-half">
                <label class="form-label" for="text-edit">Text</label>
                <textarea id="text-edit" name="content" class="form-control" rows="6" style="width:100%;"><%=obj.note%></textarea>
            </div>
            <div class="form-group edit-item type-textArea column-one-half">
                <label class="form-label" for="file-selector" >Documents (optional)</label>
                <div class="upload-target upload-target-js">
                <div>Drag and drop files here or</div>
                <label class="button button-blue" tabindex="1">Select a file<input id="file-selector" class="hidden" type="file" multiple="multiple"></label>
                </div>
            </div>
        </div>
        <ul class="file-list">
        <% for(var fileIdx in obj.documents) { var file = obj.documents[fileIdx]; %>
            <%=obj.fileLine(file)%>
        <% } %>
        </ul>
        <div class="form-group">
            <button type="submit" class="button button-blue" name="btn-action" value="create">Save</button>
            <button type="button" class="button button-grey pull-right dlg-close" value="cancel">Cancel</button>
        </div>
        </form>
        <div class="saving">
            <div class="margin-bottom-1">Saving</div>
        </div>
        </div>
    `,
    { variable: "obj" }
  );

  var dialogCompact = _.template(
    `
        <div class="note-edit">
        <form action="/case/<%=(obj.case && obj.case.id) || obj.caseId || obj.case_id %>/note/<% if(obj.id) print(obj.id + '/')%>?__prefix=<%=(obj.case && obj.case.id) || obj.caseId %>" method="post">
        <%=obj.csrfToken_input%>
        <input type="hidden" name="note_id" value="<%=obj.id%>">
        <input type="hidden" name="content_type" value="<%=obj.content_type%>">
        <input type="hidden" name="model_id" value="<%=obj.model_id%>">
        <input type="hidden" name="model_key" value="<%=obj.model_key%>">
        <div class="edit-upload-block">
            <div class="form-group edit-item type-textArea column-full upload-target-js">
                <textarea id="text-edit" name="content" class="form-control" rows="3" style="width:100%;"><%=obj.note%></textarea>
            </div>
        </div>
        <ul class="file-list">
        <% for(var fileIdx in obj.documents) { var file = obj.documents[fileIdx]; %>
            <%=obj.fileLine(file)%>
        <% } %>
        </ul>
        <div class="form-group">
            <button type="submit" class="button button-blue compact" name="btn-action" value="create">Save</button>
            <button type="button" class="button button-grey compact pull-right dlg-close" value="cancel">Cancel</button>
        </div>
        </form>
        <div class="saving">
            <div class="margin-bottom-1">Saving</div>
        </div>
        </div>
    `,
    { variable: "obj" }
  );

  var fileLine = _.template(
    `
        <li class="file-list-line <% if(!file.id) { print(" new-file") } %>" data-fileid="<%=file.id %>">
        <div class="pull-right"><a href="javascript:void(0)" class="file-delete"><i class="icon icon-bin" data-submissioncount="<%=file.submission_count%>"></i></a></div>
        <div class="pull-right select"><select class="form-control confidential">
            <option value="confidential" <% if(file.confidential) print("selected") %>>Confidential</option>
            <option value="non-confidential" <% if(!file.confidential) print("selected") %>>Non-confidential</option>
        </select></div>
        <div>
            <% if(file.safe==false) {print('<i class="icon icon-skull correct" title="This file is infected with a virus. Please remove it."></i>')} %>
            <% if(file.safe==null) {print('<i class="icon icon-amber-warning correct" title="This file is awaiting virus scanning."></i>')} %>
            <% if(file.safe && file.id) { %><a href="/document/<%=file.id%>/download/" class="link"><%=file.name%></a><% } else { %><span><%=file.name%></span><% } %>
        </div>
        </li>
        `,
    { variable: "file" }
  );

  var tmpNoteWidget = _.template(
    `
        <ul class="note-list">
        <% var notes = obj.context.notes || []; for(var note_idx=0; note_idx<notes.length; note_idx++) {
            var note = notes[note_idx]; %>
            <% print(obj.context.templates["noteLine"]({note:note, context:obj.context})); %>
        <% } %>
        </ul>
        <button class="link add-note" type="button">+ Add a note</button>
    `,
    { variable: "obj" }
  );

  var noteLine = _.template(
    `
        <li class="note">
            <textarea class="data-json hidden"><%=JSON.stringify(obj.note) %></textarea>
            <% if((!obj.note.data || !obj.note.data.system) && (obj.note.created_by.id == helpers.get(window, 'dit.user.id'))) { %>
                <div class="edit-note pull-right">
                    <button class="button-link edit-note" type="button">
                        Edit
                        <i class="icon icon-pen"></i>
                    </button>
                </div>
            <% } %>
            <div class="note-event">
                <% if(obj.note.last_modified && obj.note.last_modified != obj.note.created_at) { %>
                    <span class="nobreak" title="<%= new Date(obj.note.last_modified).format('HH:MM dd mm yyyy') %>">Modified <%= new Date(obj.note.last_modified).format('$ago') %></span>
                <% } else { %>
                    <span class="nobreak" title="<%= new Date(obj.note.created_at).format('HH:MM dd mm yyyy') %>"><%= new Date(obj.note.created_at).format('$ago') %></span>
                <% } %>
                &nbsp;by&nbsp;<%= obj.note.created_by.name %>
            </div>
            <div class="column-one-half">
                <div class="note-text markdown" data-id="<%=obj.note.id %>" data-model="note" data-multiline="true" data-name="content"><%=obj.context.sanitize(obj.note.note) %></div>
            </div>
            <div class="column-one-half">
                <ul class="note-file-list">
                    <% for(var file_idx=0;file_idx<obj.note.documents.length; file_idx++) {
                        var file = obj.note.documents[file_idx]; %>
                        <li>
                        <% if(file.confidential) { %><div class="confidential pull-right" title="This file is confidential and cannot be published or sent to any other party">Confidential</div><% } %>
                        <% if(file.safe) { %><a class="link" href="/document/<%=file.id%>/download/" title="Created <%= new Date(obj.note.created_at).format("HH:MM:SS dd mon yyyy") %>"><% } else { print('<span '); if(file.safe==null) {print('class="kit"')} print('>')}; %><%=file.name%><% if(file.safe) { print("</a>") } else { print("</span>")} %>
                        <% if(file.safe==false) {print('<i class="icon icon-skull correct" title="This file is infected with a virus. Please remove it."></i>')} %>
                        <% if(file.safe==null) {print('<div><i class="icon icon-amber-warning correct" title="This file is awaiting virus scanning."></i><span class="virus-warning"> scanning in progress.</span></div>')} %>
                        <!-- <% if(file.confidential) { %><i class="icon icon-flag correct" title="Confidential"><span class="visually-hidden">Confidential</span></i><% } %>-->
                        </li>
                    <% } %>
                </ul>
            </div>
        </li>
    `,
    { variable: "obj" }
  );

  var noteLineCompact = _.template(
    `
        <li class="note">
            <textarea class="data-json hidden"><%=JSON.stringify(obj.note) %></textarea>
            <% if(obj.note.created_by.id == (dit.user && dit.user.id)) { %>
                <div class="edit-note pull-right">
                    <button class="button-link edit-note" type="button">
                        Edit
                    </button>
                </div>
            <% } %>
            <div class="note-event">
                <div title="Created by <%=obj.note.created_by.name %>" class="circular-badge small" style="background:<%=obj.note.created_by.colour || '#000'%>"><%=obj.note.created_by.initials %></div>
                <% if(obj.note.last_modified && obj.note.last_modified != obj.note.created_at) { %>
                    <span class="nobreak" title="<%= new Date(obj.note.last_modified).format('HH:MM dd mm yyyy') %>"><%= new Date(obj.note.last_modified).format('$ago') %> (edited)</span>
                <% } else { %>
                    <span class="nobreak" title="<%= new Date(obj.note.created_at).format('HH:MM dd mm yyyy') %>"><%= new Date(obj.note.created_at).format('$ago') %></span>
                <% } %>
            </div>
            <div class="column-full">
                <div class="note-text markdown" data-id="<%=obj.note.id %>" data-model="note" data-multiline="true" data-name="content"><%=obj.context.sanitize(obj.note.note) %></div>
            </div>
            <% if(obj.note.documents && obj.note.documents.length) { %>
            <div class="column-full">
                <ul class="note-file-list">
                    <% for(var file_idx=0;file_idx<obj.note.documents.length; file_idx++) {
                        var file = obj.note.documents[file_idx]; %>
                        <li>
                            <% if(file.confidential) { %><div class="confidential pull-right" title="This file is confidential and cannot be published or sent to any other party">Confidential</div><% } %>
                            <% if(file.safe) { %><a class="link" href="/document/<%=file.id%>/download/" title="Created <%= new Date(obj.note.created_at).format("HH:MM:SS dd mon yyyy") %>"><% } else { print('<span '); if(file.safe==null) {print('class="kit"')} print('>')}; %><%=file.name%><% if(file.safe) { print("</a>") } else { print("</span>")} %>
                            <% if(file.safe==false) {print('<i class="icon icon-skull correct" title="This file is infected with a virus. Please remove it."></i>')} %>
                            <% if(file.safe==null) {print('<div><i class="icon icon-amber-warning correct" title="This file is awaiting virus scanning."></i><span class="virus-warning"> scanning in progress.</span></div>')} %>
                            <!-- <% if(file.confidential) { %><i class="icon icon-flag correct" title="Confidential"><span class="visually-hidden">Confidential</span></i><% } %>-->
                            </li>
                    <% } %>
                </ul>
            </div>
            <% } %>
        </li>
    `,
    { variable: "obj" }
  );

  function sanitize(str) {
    var span = document.createElement("span");
    span.textContent = str;
    return $(span).html().replace(/\n/g, "<br>");
  }

  function getDialog(title, data, el) {
    this.closeDialog();
    var thisDialog = this.compactMode ? dialogCompact : dialog;
    this.dialog = $(
      thisDialog(
        _.extend(
          {},
          { fileLine: fileLine, title: title },
          data || {},
          window.dit
        )
      )
    );
    this.dialog.on("click", _.bind(onDlgClick, this));
    this.note_element = el;
    if (el) {
      el.after(this.dialog);
      el.hide();
    } else {
      this.el.find("ul.note-list").append(this.dialog);
    }
    this.dialog
      .find("label.button")
      .attr("tabIndex", 0)
      .keypress(function (evt) {
        $(evt.target).trigger("click");
      });
    this.dialog.find("form").on("submit", _.bind(onSubmit, this));
    this.dialog.on("change", _.bind(onDlgChange, this));
    this.fileList = this.dialog.find(".file-list");
    this.files = data.documents;
    delete this.deleteList;
    delete this.changeList;
    this.editingElement = el;
    // set up drop target
    this.dragTarget = this.el.find(".upload-target-js");
    this.dragTarget.on("dragenter", this.onDragOver);
    this.dragTarget.on("dragover", this.onDragOver);
    this.dragTarget.on("dragend", _.bind(endDrag, this));
    this.dialog.find("textarea").focus();
  }

  function closeDialog() {
    this.dialog && this.dialog.remove();
    delete this.dialog;
    this.editingElement && this.editingElement.show();
    delete this.editingElement;
  }

  function onDlgClick(evt) {
    var self = this;
    var target = $(evt.target);
    if (target.val() == "cancel") {
      if (self.changeList || self.deleteList || self.noteChanged) {
        popups
          .confirm("Abandon your changes?", "Unsaved changes")
          .then(this.closeDialog);
      } else {
        this.closeDialog();
      }
    }
    if (target.closest("a").hasClass("file-delete")) {
      var submissionCount = target.attr("data-submissioncount");
      if (submissionCount > 0) {
        popups.alert(
          "This document is used in " +
            submissionCount +
            " submission" +
            (submissionCount > 1 ? "s" : ""),
          "Unable to delete"
        );
      } else {
        var fileEl = target.closest(".file-list-line");
        var fileId = fileEl.attr("data-fileid");
        if (fileId) {
          //popups.confirm('Are you sure you want to delete this file?').then(function() {
          (self.deleteList = self.deleteList || {})[fileId] = 1;
          //})
        }
        fileEl.remove();
      }
    }
  }

  function onDlgChange(evt) {
    var self = this;
    var target = $(evt.target);
    var fileId = target.closest(".file-list-line").attr("data-fileid");
    if (fileId && target.hasClass("confidential")) {
      (self.changeList = self.changeList || {})[fileId] = target.val();
    }
    if (target.attr("type") == "file") {
      //var files = new FormData(target.closest('form')[0]).getAll('files');
      var files = target[0].files;
      _.each(files, function (file) {
        addFile.call(self, file);
      });
    }
  }

  function addFile(file) {
    /* Add a file to the end of the file list */
    file && (file.confidential = true);
    var newEl = $(fileLine(file));
    this.fileList.append(newEl);
    newEl[0]["file"] = file;
  }

  function onSubmit(evt) {
    var self = this;
    evt.preventDefault();

    var form = this.dialog.find("form");

    var formData = new FormData(evt.target);
    var newFiles = this.dialog.find(".file-list-line.new-file");
    newFiles.each(function () {
      var file = this.file;
      var confidential = $(this).find("select.confidential").val();
      formData.append("files", file);
      formData.append("file-meta", confidential);
    });
    // Only show saving mask if there are new files - otherwise it's very quick.
    if (newFiles.length) {
      this.dialog.addClass("saving");
    }

    var data = form.serializeArray();
    var url = form.attr("action");
    _.each(this.deleteList, function (val, document_id) {
      formData.append("delete_list", document_id);
    });
    _.each(this.changeList, function (value, document_id) {
      formData.append("set_" + value, document_id);
    });
    $.ajax({
      method: "post",
      url: url,
      data: formData,
      cache: false,
      contentType: false,
      processData: false,
    }).then(
      function (note) {
        var html = (self.compactMode || true ? noteLineCompact : noteLine)({
          note: note,
          context: {
            sanitize: sanitize,
          },
        });
        self.dialog.after(html);
        self.dialog.remove();
        self.note_element && self.note_element.remove();
        self.pollForNotScanning();
      },
      function () {
        alert("Save failed");
        self.dialog.removeClass("saving");
      }
    );
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

  function onDrop(evt) {
    var self = this;
    endDrag.call(this);
    evt.preventDefault();
    var files = evt.originalEvent.dataTransfer.files;
    for (var i = 0; i < files.length; i++) {
      addFile.call(self, files[i]);
    }
  }

  function onClick(evt) {
    var target = $(evt.target).closest("button,.upload-target");
    if (target.hasClass("edit-note")) {
      // edit existing note
      var outer = target.closest("li");
      var text = outer.find(".note-text").text();
      var markdown = outer.attr("data-markdown");

      var id = outer.attr("data-id");
      try {
        var data = JSON.parse(outer.find("textarea.data-json").val());
      } catch (e) {
        console.error("Bad json", e);
      }
      getDialog.call(this, "Edit note", data, outer);
    }
    if (target.hasClass("add-note")) {
      // add new note
      getDialog.call(this, "Add note", this.getNoteContext());
    }
  }

  constructor.prototype = {
    pollForNotScanning: function () {
      var self = this;
      setTimeout(function () {
        self.getNote().then(function () {
          var scanning = self.isScanning();
          if (!self.isScanning()) {
            self.renderWidget();
          } else {
            self.pollForNotScanning();
          }
        });
      }, 2000);
    },
    isScanning: function () {
      var self = this;
      var pending = false;
      _.each(this.notes || [], function (note) {
        _.each(note.documents || [], function (document) {
          pending = pending || _.isNull(document.safe);
        });
      });
      return pending;
    },
    getContextValue: function (key) {
      var val = this.defaults[key] || "";
      if (val.indexOf("#") == 0) {
        var valName = val.substr(1);
        val = this.el.closest("form").find(`[name=${valName}]`).val();
      }
      return val;
    },

    getNoteContext: function () {
      var self = this;
      var context = {};
      _.each(this.defaults, function (value, key) {
        context[key] = self.getContextValue(key);
      });
      /*
            var model_id = context['model_id'];
            if(model_id.indexOf('#') == 0) {
                var idName = model_id.substr(1);
                var modelIdElement = this.el.closest('form').find(`[name=${idName}]`);
                var model_id =  modelIdElement.val();
                context = _.extend(context, {model_id:model_id})
            }
            */
      return context;
    },
    refresh: function () {
      var self = this;
      this.getNote().then(function () {
        if (self.isScanning()) {
          self.pollForNotScanning();
        }
        self.renderWidget();
      });
    },
    renderWidget: function () {
      var obj = {
        context: {
          notes: this.notes,
          templates: {
            noteLine: this.compactMode ? noteLineCompact : noteLine,
          },
          user: {
            id: "1234", // TODO - Get real thing
          },
          sanitize: sanitize,
        },
      };
      var html = tmpNoteWidget(obj);
      this.el.html(html);
    },
    getNote: function () {
      var self = this;
      var case_id = window.dit.caseId;
      var context = this.getNoteContext();
      self.notes = {};
      return new Promise(function (resolve, reject) {
        $.ajax({
          method: "GET",
          url:
            "/case/" +
            context.case_id +
            "/note/" +
            context.content_type +
            "/" +
            context.model_id +
            "/" +
            (context.model_key ? context.model_key + "/" : ""),
        }).then(
          function (notes) {
            if (self.defaults.model_key) {
              self.notes =
                helpers.index(notes, "model_key")[self.defaults.model_key] ||
                [];
            } else {
              self.notes = notes;
            }
            resolve();
          },
          function () {
            reject();
          }
        );
      });
    },
  };

  return constructor;
});
