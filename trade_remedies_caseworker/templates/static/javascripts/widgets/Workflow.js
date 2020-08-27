define(["modules/helpers", "modules/popUps", "modules/moment.min"], function (
  helpers,
  popups,
  moment
) {
  "use strict";

  function isDisabled(task) {
    var permission = task.permission;
    if (!task.active || (permission && !(permission in this.permissions))) {
      return ' disabled="1" ';
    }
  }

  var templateStrings = {};

  templateStrings["Checkbox/NA"] =
    '\
        <% if(obj.store.last_type !=  obj.task.response_type.name) {\
            obj.store.last_type =  obj.task.response_type.name; %>\
            <div class="form-group edit-item header-row inline">\
                <div class="grid-row">\
                    <div class="column-one-half">\
                        &nbsp;\
                    </div>\
                    <div class="column-one-half">\
                        <label>Yes</label><label>N/A</label>\
                    </div>\
                </div>\
            </div>\
        <% } %>\
        <legend class="visually-hidden"><%= obj.task.label %></legend>\
        <div class="column-one-half">\
            <label class="form-label dim-on-disable"><%= obj.task.label %></label>\
        </div>\
        <div class="column-one-half">\
            <div class="multiple-choice">\
                <input id="<%= obj.task.key %>" type="checkbox" name="<%= obj.task.key %>" value="yes" <% if(obj.value == "yes") { %> checked="checked"<% } %> <% if(obj.value == "na") { %> disabled="disabled"<% } %> <% print(obj.isDisabled(obj.task)); %> >\
                <label for="<%= obj.task.key %>" class="dim-on-disable"><span class="visually-hidden">Yes</span></label>\
            </div>\
            <div class="multiple-choice">\
                <input id=<%=obj.task.key%>-na class="na-check" data-attach="NotApplicable" type="checkbox" name="<%= obj.task.key %>" value="na" <% if (obj.value == "na") { print("checked=\'checked\'") } %> <% print(obj.isDisabled(obj.task)); %> >\
                <label for="<%= obj.task.key %>-na"><span class="visually-hidden">N/A</span></label>\
            </div>\
        </div>';

  templateStrings["Checkbox"] =
    '\
        <% if(obj.store.last_type !=  obj.task.response_type.name) {\
            obj.store.last_type =  obj.task.response_type.name; %>\
        <% } %>\
        <legend class="visually-hidden"><%= obj.task.label %></legend>\
        <div class="column-one-half">\
            <label class="form-label dim-on-disable"><%= obj.task.label %></label>\
        </div>\
        <div class="column-one-half">\
            <div class="multiple-choice">\
                <input id="<%= obj.task.key %>" type="checkbox" name="<%= obj.task.key %>" value="yes" <% if(obj.value == "yes") { %> checked="checked"<% } %> <% if(obj.value == "na") { %> disabled="disabled"<% } %> <% print(obj.isDisabled(obj.task)); %> >\
                <label for="<%= obj.task.key %>" ><span class="visually-hidden">Yes</span></label>\
            </div>\
        </div>';

  templateStrings["Yes/No"] =
    '\
        <legend class="visually-hidden"><%= obj.task.label %></legend>\
        <div class="column-one-half">\
            <label class="form-label"><%=obj.task.label %></label>\
        </div>\
        <div class="column-one-half">\
            <div class="multiple-choice">\
                <input id="<%=obj.task.key %>-1" type="radio" name="<%=obj.task.key %>" value="yes" <% if(obj.value == "yes") { %> checked="checked" <% } %><% print(obj.isDisabled(obj.task)); %> >\
                <label for="<%=obj.task.key %>-1">Yes</label>\
            </div>\
            <div class="multiple-choice">\
                <input id="<%= obj.task.key %>-2" type="radio" name="<%= obj.task.key %>" value="no" <% if(obj.value == "no") { %> checked="checked" <% } %> <% print(obj.isDisabled(obj.task)); %> >\
                <label for="<%= obj.task.key %>-2">No</label>\
            </div>\
        </div>';

  templateStrings["Free Text"] =
    '\
        <div class="column-one-half">\
            <label class="form-label" for="<%=obj.task.key %>"><%= obj.task.label %></label>\
        </div>\
        <div class="column-one-half">\
            <input id="<%=obj.task.key %>" type="text" class="form-control" name="<%=obj.task.key %>"  value="<% if(obj.value != "na") { print(obj.value || "")} %>" <% print(obj.isDisabled(obj.task)); %> >\
        </div>';

  templateStrings["Date"] =
    '\
        <div class="column-one-half">\
            <label class="form-label" for="<%=obj.task.key %>"><%= obj.task.label %></label>\
        </div>\
        <div class="column-one-half">\
            <input id="<%=obj.task.key %>" type="text" class="form-control" data-attach="DatePicker" name="<%=obj.task.key %>"  value="<% if(obj.value != "na") { print(obj.value || "")} %>" <% print(obj.isDisabled(obj.task)); %> >\
        </div>';

  templateStrings["Text area"] =
    '\
        <div class="column-full">\
            <label class="form-label" for="<%=obj.task.key %>"><%= obj.task.label %></label>\
            <textarea id="<%=obj.task.key %>" class="form-control" name="<%=obj.task.key %>" <% print(obj.isDisabled(obj.task)); %> ><% if(obj.value != "na") { print(obj.value || "")} %></textarea>\
        </div>';

  templateStrings["undefined"] =
    '\
        <div class="column-full hidden">\
             <span>Task - <%=(obj.task.response_type && obj.task.response_type.name) || "no name"%></span>\
        </div>';

  templateStrings["Label"] =
    '\
        <div class="column-full">\
            <label class="form-info"><%=obj.context.makeHtml(obj.task.label) %></label>\
        </div>';

  templateStrings["NoteSection"] =
    '\
        <div class="note-widget" data-attach="NoteWidget" data-model-id="<%=obj.state.id%>" data-content-type="cases.caseworkflow" data-model-key="<%=obj.task.key%>">\
        </div>';

  var taskPage = _.template(
    '\
        <form class="dd-form action-form">\
        <input type="hidden" name="action-key" value="<%=action.key%>">\
        <div class="column-full nav">\
        <h2 class="heading-large"><%= action.label %></h2>\
        <% for(var idx = 0; idx<tasks.length; idx++) {\
            var task = tasks[idx];\
            var valArray = state[task.key];\
            var value = (valArray || [])[0]; %>\
            <fieldset class="form-group edit-item inline <% if(value=="na") { %> disabled<% } %>">\
                <div class="grid-row">\
                <%\
                var name = task.response_type && task.response_type.name; \
                print((control_templates[name] || control_templates["undefined"])({task:task, value:value, store:store, isDisabled:isDisabled, state: state, context: context}));\
                %>\
                </div>\
            </fieldset>\
        <% } %>\
        <div class="form-group edit-item type-radioset">\
            <button class="button button-blue pull-left save" value="save-progress" name="btnAction" type="button">Save and Exit</button>\
            <button class="button button-grey pull-right cancel" value="-" name="btnAction" type="button">Cancel</button>\
        <!--    <a class="button button-grey pull-right" href="#">Cancel</a> -->\
        </div>\
        </div>\
        </form>\
    '
  );

  var constructor = function (el) {
    this.el = el;
    this.workflow = JSON.parse(this.el.find("#workflow-json").val());
    this.workflowIndex = indexWorkflow(this.workflow.root);
    this.permissions = JSON.parse(this.el.find("#permissions-json").val());
    this.state = JSON.parse(this.el.find("#state-json").val());
    this.target_block = el.find(el.attr("data-target-block"));
    this.caseId = el.attr("data-case");
    this.el.on("click", _.bind(onClick, this));
    this.makeHtml = makeHtml;
    //getNote.call(this);
    $(window).on("hashchange", _.bind(onHashChange, this));
    this.format_date = format_date;
    onHashChange.call(this); // in case we link straight to a task page
  };

  function indexWorkflow(workflow) {
    var index = {};
    function indexWorkflowInner(level) {
      _.each(level, function (action) {
        index[action.key] = action;
        indexWorkflowInner(action.children);
      });
    }
    indexWorkflowInner(workflow);
    return index;
  }

  function format_date(date, format) {
    return moment(date).format(format || "MMM Do YYYY");
  }

  function updateStatusWidget() {
    var self = this;
    var widget = $(".case-summary");
    var state = this.state;
    var value, arr;
    widget.find("[data-statekey]").each(function () {
      var $el = $(this);
      if ((arr = self.state[$el.attr("data-statekey")])) {
        arr = _.isArray(arr) ? arr : [arr];
        switch ($el.attr("data-type")) {
          case "date":
            value = arr[1] && format_date(arr[1], "DD MMM YYYY");
            break;
          case "lookup":
            value = (self.workflowIndex[arr[0]] || {}).label || "n/a";
            break;
          default:
            value = arr[0];
        }
        $(this).text(value || "");
      }
    });
  }

  function onHashChange(evt) {
    var hash = window.location.hash.substr(1, 30);
    if (hash) {
      renderTaskpage.call(this, hash);
    } else {
      // cancel
      this.target_block.html("");
      this.target_block.parent().removeClass("show-block");
    }
  }

  function serializeArray(els) {
    // Replace the jquery serializer with one that includes disabled controls
    var out = [];
    els.each(function () {
      var $el = $(this);
      var name = $el.attr("name");
      if (name) {
        var val = $el.val();
        if ($el.attr("type") in { radio: 1, checkbox: 1 }) {
          if ($el.prop("checked")) {
            out.push({ name: name, value: val });
          }
        } else {
          out.push({ name: name, value: val });
        }
      }
    });
    return out;
  }

  function onClick(evt) {
    var self = this;
    var target = $(evt.target);
    var key = target.attr("data-id");
    var isTask = !!target.attr("data-target-block");
    if (target.hasClass("cancel")) {
      window.location.assign("#");
    }
    if (target.hasClass("save")) {
      evt.preventDefault();

      var form = self.target_block.find("form");
      //var data = $(form).find('input[type=hidden],:input:not(:hidden)').serializeArray(1);
      var data = serializeArray(
        $(form).find("input[type=hidden],:input:not(:hidden)")
      );
      data.push({ name: "csrfmiddlewaretoken", value: window.dit.csrfToken });
      $.ajax({
        method: "POST",
        url: "/case/" + self.caseId + "/action/" + self.action.id + "/",
        data: data,
        //dataType: 'json'
      }).then(
        function (result) {
          if (result.workflow_state) {
            _.extend(self.state, result.workflow_state);
            indexActions.call(self);
            updateStatusWidget.call(self);
          }
        },
        function () {
          alert("Failure");
        }
      );
      window.location.assign("#"); // close the pane first
    }
  }

  var tmpStatus = _.template(
    '\
        <% if(value == "complete") { %>\
            <strong class="task-completed">Completed</strong>\
        <% } else { %>\
            <% if(value == "in-progress") { %>\
                <strong class="task-completed progress">In progress</strong>\
            <% } %>\
            <% if(due_date) { %>\
                <span class="due-date pull-right"><span class="grey">due:</span>&nbsp;<%=format_date(due_date, "DD MMM YYYY") %></span>\
            <% } %>\
        <% } %>\
        '
  );

  function indexActions() {
    // find all the rendered action objects ready to
    var self = this;
    this.el.find("div[data-action]").each(function () {
      var el = $(this);
      var actionKey = el.attr("data-action");
      var val = self.state[actionKey];
      if (val) {
        var html = tmpStatus({
          value: val[0],
          due_date: val[1],
          format_date: self.format_date,
        });
        el.find(".state-container").html(html);
      }
    });
  }

  function makeHtml(inStr) {
    return $("<div>").text(inStr).html().replace("\n", "<br>");
  }

  function renderTaskpage(key) {
    var action = this.workflowIndex[key];
    var self = this;
    var store = {}; // used by templates to store informtaion
    if (!this.control_templates) {
      // need to compile the templates
      this.control_templates = {};
      _.each(templateStrings, function (str, key) {
        self.control_templates[key] = _.template(str, { variable: "obj" });
      });
    }
    self.action = action;

    var content = taskPage({
      action: action,
      tasks: action.children,
      last_type: "",
      state: this.state,
      store: store,
      isDisabled: _.bind(isDisabled, this),
      control_templates: self.control_templates,
      context: self,
    });

    self.target_block.html("");
    self.target_block.append($(content));
    self.target_block.attachWidgets();
    self.target_block.parent().addClass("show-block");
  }

  return constructor;
});
