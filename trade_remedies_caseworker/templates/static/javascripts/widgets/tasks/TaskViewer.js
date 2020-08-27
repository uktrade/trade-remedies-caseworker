define(["modules/helpers", "modules/popUps"], function (helpers, popups) {
  "use strict";

  var templateStrings = {
    create_dialogue: `
            <div class="compact-form">
                <form class="task-form">
                    <div class="column-full">
                        <h1 class="heading-small">Create a task</h1>
                        <input type="hidden" name="case_id" value="<%=dit.caseId%>">
                        <input type="hidden" name="id">
                    </div>
                    <div class="column-one-half">
                        <%=obj.templates.input({name:'name',label:'Name'})%>
                    </div>
                    <div class="column-one-half">
                        <%=obj.templates.date({name:'due_date',label:'Due date'})%>
                    </div>
                    <div class="column-full">
                        <%=obj.templates.text({name:'description',label:'Description'})%>
                    </div>
                    <div class="column-one-half">
                        <%=obj.templates.select({name:'priority',label:'Priority',options:[{key:'high',name:'High'},{key:'medium',name:'Medium'},{key:'low',name:'Low'}]})%>
                        <input type="hidden" name="status" value="todo">
                        <%=obj.templates.input({name:'data_estimate',label:'Points estimate'})%>
                    </div>
                    <div class="column-one-half">
                        <%=obj.templates.select({name:'assignee_id',label:'Assignee',options:obj.self.assignees})%>
                    </div>
                    <div class="column-full">
                        <div class="content-widget" data-attach="ContentTypeLink"></div>
                    </div>
                    <div class="column-full margin-top-1">
                        <button class="button button-blue dlg-close no-debounce" name="btn-action" value="save">Save</button>
                        <button class="button button-grey pull-right dlg-close">Cancel</button>
                    </div>
                </form>
            </div>
        `,
    create_nwd_dialogue: `
            <div class="compact-form">
                <form class="task-form">
                    <input type="hidden" name="status" value="nwd">
                    <div class="column-full">
                        <h1 class="heading-small">Create a non-working period</h1>
                    </div>
                    <div class="column-half">
                        <%=obj.templates.input({name:'name',label:'Name'})%>
                    </div>
                    <div class="column-full">
                        <%=obj.templates.text({name:'description',label:'Description'})%>
                    </div>
                    <div class="column-one-half">
                        <%=obj.templates.date({name:'data_start_date',label:'Start date'})%>
                    </div>
                    <div class="column-one-half">
                        <%=obj.templates.date({name:'due_date',label:'End date'})%>
                    </div>
                    <div class="column-one-half">
                        <%=obj.templates.select({name:'assignee_id',label:'Who?',options:obj.self.assignees, noBlank:true})%>
                    </div>
                    <div class="column-full margin-top-1">
                        <button class="button button-blue dlg-close no-debounce" name="btn-action" value="save">Save</button>
                        <button class="button button-grey pull-right dlg-close">Cancel</button>
                    </div>
                </form>
            </div>
        `,
    modal_nwd_viewer: `
            <div class="task-viewer nwd">
                <form class="task-form">
                    <input type="hidden" name="id">
                    <div class="form-row">
                        <div class="in-place-edit bold placeholder-name" data-attach="EditInPlace2" name="name"></div>
                        <div class="in-place-edit small-font placeholder-description" data-attach="EditInPlace2" name="description" data-multiline="true"></div>
                    </div>
                    <div class="form-row">
                        <div class="form-half left">
                            <%=obj.templates.date({name:'data_start_date',label:'Start date'})%>
                        </div>
                        <div class="form-half right">
                            <%=obj.templates.date({name:'due_date',label:'End date'})%>
                        </div>
                    </div>
                    <div class="form-half left">
                        <label class="form-label"><span>Assignee</span>
                            <div name="assignee" class="margin-top-5px"></div>
                        </label>
                    </div>
                    <div class="form-half right">
                        <button type="button" class="icon icon-bin pull-right margin-right-1 margin-top-1" value="delete" title="Delete non-working period"></button>
                    </div>
                </form>
            </div>
        `,
    task_viewer_form: `
            <form class="task-form">
                <input type="hidden" name="id">
                <div class="in-place-edit bold placeholder-name" data-attach="EditInPlace2" name="name"></div>
                <div class="in-place-edit small-font placeholder-description" data-attach="EditInPlace2" name="description" data-multiline="true"></div>
                <div class="form-row">
                    <div class="form-half left">
                        <%=obj.templates.select({name:'assignee_id',label:'Assignee',options:obj.self.assignees})%>
                        <%=obj.templates.select({name:'status',label:'Status',options:[{key:'todo',name:'To do'},{key:'inprogress',name:'In progress'},{key:'done',name:'Done'}]})%>
                    </div>
                    <div class="form-half right">
                        <%=obj.templates.date({name:'due_date',label:'Due date'})%>
                        <!-- <%=obj.templates.date({name:'data_start_date',label:'Start date'})%> -->
                        <%=obj.templates.select({name:'priority',label:'Priority',options:[{key:'high',name:'High'},{key:'medium',name:'Medium'},{key:'low',name:'Low'}]})%>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-half left">
                        <%=obj.templates.input({name:'data_estimate',label:'Points estimate'})%>
                        <!-- <%=obj.templates.select({name:'data_estimate',label:'Estimate (points)',options:[{key:'1',name:'1'},{key:'2',name:'2'},{key:'3',name:'3'},{key:'5',name:'5'},{key:'8',name:'8'},{key:'13',name:'13'},{key:'21',name:'21'}]})%> -->
                    </div>
                    <div class="form-half right">
                        <%=obj.templates.input({name:'data_remaining',label:'Points remaining'})%>
                        <!--<%=obj.templates.select({name:'data_remaining',label:'Remaining (points)',options:[{key:'1',name:'1'},{key:'2',name:'2'},{key:'3',name:'3'},{key:'5',name:'5'},{key:'8',name:'8'},{key:'13',name:'13'},{key:'21',name:'21'}]})%> -->
                    </div>
                </div>
                <!-- <div class="form-row">
                    <div class="form-half left">
                        <label class="form-label" for="content">
                            <span>Effort (man days)</span>
                            <div class="in-place-edit placeholder" data-attach="EditInPlace2" name="data_estimate"></div>
                        </label>
                    </div>
                    <div class="form-half right">
                        <label class="form-label" for="content">
                            <span>Points remaining</span>
                            <div class="in-place-edit placeholder" data-attach="EditInPlace2" name="data_remaining"></div>
                        </label>
                    </div>
                </div> -->
                <div class="content-widget margin-top-1" data-attach="ContentTypeLink" data-mode="view">
                    <input type="hidden" name="case_id">
                    <input type="hidden" name="content_type">
                    <input type="hidden" name="model_id">
                    <input type="hidden" name="model_key">
                </div>
                <div class="form-group">
                    <div class="note-widget compact" data-attach="NoteWidget" data-model-id="#id" data-content-type="tasks.task" data-case-id="#case_id"></div>
                </div>
            </form>
        `,
    task_viewer: `
            <div class="task-viewer">
                <a class="close pull-left"><i class="icon icon-left"></i></a><div class="bold pull-left" name="reference_string"></div><button type="button" class="icon icon-bin pull-right margin-right-1" value="delete"></button>
                <div class="task-viewer-client" data-attach="ScrollShadow">
                    <%=obj.templates.task_viewer_form(obj) %>
                </div>
            </div>
        `,
    modal_task_viewer: `
            <div class="compact-form task-viewer">
                    <input type="hidden" name="case_id" value="<%=dit.caseId%>">
                    <input type="hidden" name="id">
                    <div><span name="case.reference"></span> <span name="case.name"></span></div>
                    <div class="bold"><span name="reference_string"></span></div>
                     <%=obj.templates.task_viewer_form(obj) %>
                </form>
            </div>
        `,
    input: `
            <label class="form-label" for="content"><span class><%=obj.label%></span>
                <input id="<%=obj.name%>" type="text" class="form-control" name="<%=obj.name%>">
            </label>
        `,
    text: `
            <label class="form-label" for="content"><span><%=obj.label%></span>
                <textarea class="form-control compact" name="<%=obj.name%>"></textarea>
            </label>
        `,
    date: `
            <label class="form-label" for="content"><span><%=obj.label%></span>
                <input type="text" class="form-control" data-attach="DatePicker" name="<%=obj.name %>" >
            </label>
        `,
    userBadge: `
            <div title="<%=obj.name%>" class="circular-badge small" style="background:<%=obj.colour || 'black' %>"><%=obj.initials%></div>
        `,
    select: `
            <label class="form-label" for="content"><span><%=obj.label%></span>
                <select class="form-control" name="<%=obj.name %>" <% if(obj.disabled) print('disabled="true"') %> >
                <% if(!obj.noBlank) { %>
                    <option value="">Please select...</option>
                <% } %>
                <% var idx; for(idx in obj.options) { var option=obj.options[idx] %>
                    <option value="<%=option.key%>"><%=option.name%></option>
                <% } %>
                </select>
            </label>
        `,
  };

  function constructor(controller, container) {
    this.controller = controller;
    this.container = container;
    this.formChange = _.bind(onFormChange, this);
    this.templates = {};
    this.onClick = _.bind(onTargetClick, this);
    _.each(
      templateStrings,
      function (str, key) {
        this.templates[key] = _.template(str, { variable: "obj" });
      },
      this
    );
  }

  function onFormChange(evt) {
    var name = $(evt.target).attr("name");
    var form = $(evt.target).closest("form");
    if (form.hasClass("task-form")) {
      this.saveViewer(form, "save", name);
    }
  }

  function onTargetClick(evt) {
    // a click on the target area
    var self = this;
    var $target = $(evt.target);
    var val = $target.val();
    if (val in { save: 1, delete: 1 }) {
      // create a task
      evt.preventDefault();
      if (val == "delete") {
        popups
          .confirm(`Are you sure you want to delete this ${self.itemName()}?`)
          .then(function () {
            self
              .saveViewer($target.closest(".task-viewer").find("form"), val)
              .then(function () {
                self.closeViewer();
                popups.notify(`Deleted ${self.itemName()}`);
              });
          });
      } else {
        self.saveViewer($target.closest("form"), val);
      }
    }
    if ($target.closest(".close").length) {
      self.closeViewer();
    }
  }

  constructor.prototype = {
    itemName: function () {
      return this.nwd ? "non working period" : "task";
    },

    getTemplate: function (templateName, params) {
      var self = this;

      function render() {
        self.templateCache = self.templateCache || {};
        self.templateCache[templateName] = self.templates[templateName]({
          templates: self.templates,
          self: self,
          params: params || {},
        });
        return self.templateCache[templateName];
      }

      return new Promise(function (resolve, reject) {
        // get the case team to allow selection of assignee
        if (!window.dit.caseId) {
          // can't get team if we're not in a case
          self.assignees = [{ key: dit.user.id, name: dit.user.name }];
          if (dit.user.hoi) {
            self.assignees.push({ key: "", name: "Everyone" });
          }
        }
        if (!self.assignees) {
          self.assignees = [];
          $.ajax({
            method: "get",
            dataType: "json",
            url: `/case/${window.dit.caseId}/team/json/`,
          }).then(
            function (results) {
              _.each(results, function (result) {
                self.assignees.push({
                  key: result.user.id,
                  name: result.user.name,
                });
              });
              self.assignees.sort(function (a, b) {
                return a.name.localeCompare(b.name);
              });
              resolve(render());
            },
            function () {
              self.assignees = [];
              resolve(render());
            }
          );
        } else {
          resolve(render());
        }
      });
    },

    populateForm: function (form, data) {
      // populate form elements from supplied data
      var self = this;
      var dataReg = /^data_(.*)$/;
      form.find("[name]").each(function () {
        var $el = $(this);
        var tag = $el.prop("tagName");
        var name = $el.attr("name");
        var reg = dataReg.exec(name);
        var thisData = data;
        if (reg) {
          name = reg[1];
          thisData = data.data || {};
        }
        var value = helpers.get(thisData, name) || "";
        switch (tag) {
          case "INPUT":
          case "TEXTAREA":
          case "SELECT":
            $el.val(value);
            break;
          case "DIV":
          case "SPAN":
            $el.html(self.makeHtml(value));
        }
        var controllerName = $el.attr("data-attach");
        if (controllerName) {
          var controller = $el[0][controllerName];
          if (_.isObject(controller) && controller["_change"]) {
            controller._change();
          }
        }
      });

      // Generate the link to the TRS page
      var contentTypeWidget = form.find(".content-widget")[0];
      if (contentTypeWidget) {
        (contentTypeWidget["ContentTypeLink"] || {}).refresh &&
          contentTypeWidget["ContentTypeLink"].refresh();
      }

      // Load and display notes
      var noteEl = form.find(".note-widget")[0];
      if (noteEl) {
        (noteEl["NoteWidget"] || {}).refresh && noteEl["NoteWidget"].refresh();
      }
    },

    createTask: function () {
      var self = this;
      self.nwd = false;
      var assignees = [];
      var stateId;
      if (dit.page == "actions") {
        // get the id of the workflow from the page
        var state = JSON.parse($("#state-json").val()) || {};
        stateId = state.id;
        var actionKey = location.hash.replace("#", "");
      }
      require(["modules/Lightbox"], function (Lightbox) {
        self
          .getTemplate("create_dialogue", { actionStateId: stateId })
          .then(function (content) {
            self.dlg = new Lightbox({
              content: content,
              buttons: { ok: 1, cancel: 1 },
            });
            self.dlg.getContainer().attachWidgets().on("click", self.onClick);
          });
      });
    },

    createNwd: function () {
      var self = this;
      self.nwd = true;
      require(["modules/Lightbox"], function (Lightbox) {
        self.getTemplate("create_nwd_dialogue").then(function (content) {
          self.dlg = new Lightbox({
            content: content,
            buttons: { ok: 1, cancel: 1 },
          });
          self.dlg.getContainer().attachWidgets().on("click", self.onClick);
        });
      });
    },

    getTask: function (taskId, noSlide) {
      var self = this;
      return new Promise(function (resolve, reject) {
        var data = {
          fields: JSON.stringify({
            Task: {
              reference_string: 0,
              id: 0,
              case_id: 0,
              name: 0,
              description: 0,
              priority: 0,
              due_date: "date",
              created_by: {
                name: 0,
              },
              case: {
                name: 0,
                reference: 0,
              },
              status: 0,
              data: 0,
              assignee_id: 0,
              assignee: {
                name: 0,
                initials: 0,
                colour: 0,
              },
              content_type: 0,
              model_id: 0,
              model_key: 0,
            },
          }),
        };
        $.ajax({
          method: "get",
          url: `/tasks/${taskId}/`,
          data: data,
        }).then(
          function (result) {
            var tasks = helpers.get(result, "result.tasks") || [];
            if (tasks.length) {
              self.showTask(tasks[0], noSlide).then(function () {
                resolve();
              });
            } else {
              reject();
            }
          },
          function (er, er2) {
            debugger;
            reject();
          }
        );
        if (self.container) {
          window.localStorage["viewing_task"] = taskId;
        }
      });
    },

    getViewer: function () {
      var self = this;
      return new Promise(function (resolve, reject) {
        if (self.$viewer && self.nwd == self.$viewer.children(".nwd").length) {
          resolve(self.$viewer);
        } else {
          self.$viewer = self.container;
          self
            .getTemplate(
              self.nwd
                ? "modal_nwd_viewer"
                : self.container
                ? "task_viewer"
                : "modal_task_viewer"
            )
            .then(function (content) {
              if (!self.container || self.nwd) {
                // open the viewer in a modal
                require(["modules/Lightbox"], function (Lightbox) {
                  self.dlg = new Lightbox({
                    content: content,
                    addClose: true,
                  });
                  self.dlg
                    .getContainer()
                    .attachWidgets()
                    .on("click", self.onClick)
                    .on("change", self.formChange);
                  resolve(self.dlg.getContainer());
                });
              } else {
                self.$viewer.html(content);
                self.$viewer
                  .attachWidgets()
                  .children(".task-viewer")
                  .on("click", self.onClick)
                  .on("change", self.formChange);
                resolve(self.$viewer);
              }
            });
        }
      });
    },

    saveViewer: function (form, button_val, name) {
      var self = this;
      return new Promise(function (resolve, reject) {
        var data = helpers.unMap(
          helpers.serializeArray(
            form.find("input, textarea, select, .in-place-edit")
          )
        );
        if (name && name in data) {
          var newData = { id: data["id"] };
          newData[name] = data[name];
          data = newData;
        }
        data["csrfmiddlewaretoken"] = window.dit.csrfToken;
        data["btn_value"] = button_val;
        $.ajax({
          method: "post",
          dataType: "json",
          url: "/tasks/",
          data: data,
        }).then(function (result) {
          resolve();
          if (!data["id"]) {
            popups.notify(`Created ${self.itemName()}`);
          }
          self.controller.renderTaskList(true);
        });
      });
    },

    closeViewer: function () {
      delete window.localStorage["viewing_task"];
      this.$viewer && this.$viewer.removeClass("open");
      if (this.dlg) {
        this.dlg.close();
        delete this.dlg;
      }
      // TODO: decouple this
      this.controller.$gridContainer.find(".selected").removeClass("selected");
      this.controller.$gridContainer.removeClass("truncate");
    },

    showTask: function (task, noSlide) {
      var self = this;
      return new Promise(function (resolve, reject) {
        self.nwd = task.status == "nwd";
        self.selected = {};
        self.selected[task.id] = 1;
        self.getViewer().then(function (viewer) {
          if (noSlide) {
            viewer.addClass("open");
          }
          self.slideMode = self.controller.settings.viewerMode != "bottom";
          viewer.find(".task-viewer").setClass("slide", self.slideMode);
          self.populateForm(viewer, task);
          viewer.show();
          setTimeout(function () {
            viewer.addClass("open");
            self.controller.$gridContainer.setClass(
              "truncate",
              !self.slideMode
            );
          }, 0);
          resolve();
        });
      });
    },

    makeHtml: function (inStr, maxlength) {
      if (_.isObject(inStr)) {
        return this.templates.userBadge(inStr);
      }
      var text = $("<div>").text(inStr).html();
      if (maxlength && text.length > maxlength) {
        text = text.substr(0, maxlength) + "...";
      }
      return text.replace(/\n/g, "<br>");
    },
  };

  return constructor;
});
