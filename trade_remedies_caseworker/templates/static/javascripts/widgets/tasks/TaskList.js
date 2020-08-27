define(["modules/helpers", "widgets/tasks/TaskData"], function (
  helpers,
  taskData
) {
  "use strict";

  var templateStrings = {
    taskTable: `
            <table class="sortable">
                <thead><tr>
                    <th data-field="ref" style="width:72px">Ref</th>
                    <th>Task</th>
                    <th data-field="assignee" style="width:64px">Who</th>
                    <th data-field="due" style="width:105px">Due</th>
                    <th style="width:64px">Pts</th>
                    <th style="width:60px">Pty</th>
                </tr></thead>
                <tbody>
                </tbody>
            </table>
        `,
    taskListInner: `
            <%
            var outOfCase = !window.dit.caseId; 
            for(var idx=0;idx<obj.tasks.length;idx++ ) {
                var task = obj.tasks[idx];
            %>
                <tr data-id="<%=task.id%>" <% if(obj.self.isSelected(task.id)) {print('class="selected"');} %> >
                <td><a href="javascript:void(0)"><% if(outOfCase) {print(helpers.get(task,'case.reference'),'-');} %><%=task.reference_string%></a></td>
                <td><%=task.name||'Un-named task'%></td>
                <td><%=task.assignee ? obj.self.controller.templates.userBadge(task.assignee) : '-'%></td>
                <td sortval="<%=task.due_date%>"><span title="<%= new Date(task.due_date).format('dd mon yyyy')%>"><% if(task.due_date) { print(new Date(task.due_date).format('$due')) } %></span></td>
                <td sortval="<%=obj.self.pointsQuot(task, true)%>"><%=obj.self.pointsQuot(task)%></td>
                <td sortval="<%={'high':'A','medium':'B','low':'C'}[task.priority] || 'D' %>"><% if(task.priority) { %><i class="pull-right clear margin-top-5px priority-icon <%= task.priority%>" title="Priority <%= task.priority%>"></i><% } %></td>
                <!-- <td sortval="<%={'todo':'A','inprogress':'B','done':'C'}[task.status] || 'D' %>"><%=task.status%></td> -->
                </tr>
            <% } %>
        `,
    nwdTable: `
            <table class="sortable nwd">
                <thead><tr>
                    <th data-field="assignee" style="width:90px">Who</th>
                    <th>Item</th>
                    <th style="width:150px">Start date</th>
                    <th style="width:150px">End date</th>
                </tr></thead>
                <tbody>
                </tbody>
            </table>
            <button class="link add-nwd no-debounce margin-top-1">+ New non working period</button>
        `,
    nwdListInner: `
            <% for(var idx=0;idx<obj.tasks.length;idx++ ) {
                var task = obj.tasks[idx];
            %>
                <tr data-id="<%=task.id%>" <% if(obj.self.isSelected(task.id)) {print('class="selected"');} %> >
                <td><%=task.assignee ? obj.self.controller.templates.userBadge(task.assignee) : 'All'%></td>
                <td><%=task.name||'Un-named period'%></td>
                <td sortval="<%=task.data.start_date%>"><span title="<%= new Date(task.data.start_date).format('dd mon yyyy')%>"><% if(task.data.start_date) { print(new Date(task.data.start_date).format('dd mon yyyy')) } %></span></td>
                <td sortval="<%=task.due_date%>"><span title="<%= new Date(task.due_date).format('dd mon yyyy')%>"><% if(task.due_date) { print(new Date(task.due_date).format('dd mon yyyy')) } %></span></td>
                </tr>
            <% } %>
        `,
    taskCardView: `
            <% for(var idx=0;idx<obj.tasks.length;idx++ ) { var task = obj.tasks[idx]; %>
                <div class="task-card <% if(obj.self.isSelected(task.id)) {print('selected');} %>" data-id="<%=task.id%>">
                    <% if(task.due_date) { %>
                        <div class="date-small pull-right <% if((new Date(task.due_date)) < (new Date())) {print('overdue')} %>" title="<%= new Date(task.due_date).format('dd mon yyyy')%>"><%= new Date(task.due_date).round().format('$due')%></div>
                    <% } %>
                    <% if(task.priority) { %>
                    <i class="pull-right clear margin-top-5px priority-icon <%= task.priority%>" title="Priority <%= task.priority%>"></i>
                    <% } %>
                    <div class="assignee"><%=task.assignee ? obj.self.controller.templates.userBadge(task.assignee) : '-'%></div>
                    <h2 class="reference bold"><%= dit.caseId ? '' : helpers.get(task,'case.reference')+'-' %><%=task.reference_string%></h2>
                    <h2 class="title -in-place-edit" data-attach="EditInPlace2" data-model="task" data-id="<%=task.id%>" data-name="name"><%=task.name||'Un-named task'%></h2>
                    <div class="description"><%=obj.self.makeHtml(task.description,200,'Add a description') %></div>
                    <% if (task.status != 'todo') { %>
                    <div class="progress-bar"><div style="width:<%=obj.self.percentDone(task) %>%;"></div></div>
                    <% } %>
                </div>
            <% } %>
        `,
    caseFilter: `
            <% for(var idx=0; idx<obj.cases.length; idx++) {
                var _case = obj.cases[idx];
            %>
            <div class="task-count <%=_case.reference in (obj.self.controller.activeFilters || {}) ? 'selected' : '' %>" data-key="<%=_case.reference %>"><%=_case.reference %><span class="count circular-badge small"><%=_case.taskCount%></span></div>
            <% } %>
        `,
  };

  function constructor(controller, el) {
    this.el = el;
    this.$gridContainer = this.el.find(".tasklist");
    this.controller = controller;
    this.templates = {};
    _.each(
      templateStrings,
      function (str, key) {
        this.templates[key] = _.template(str, { variable: "obj" });
      },
      this
    );
  }

  function sortFn(field, rev) {
    if (rev) {
      return function (a, b) {
        var A = a[field],
          B = b[field];
        return A == B ? 0 : A < B ? 1 : -1;
      };
    }
    return function (a, b) {
      var A = a[field],
        B = b[field];
      return A == B ? 0 : A < B ? -1 : 1;
    };
  }

  constructor.prototype = {
    isSelected: function (task_id) {
      return task_id in (this.selected || {});
    },

    makeHtml: function (inStr, maxlength) {
      var text = $("<div>").text(inStr).html();
      if (maxlength && text.length > maxlength) {
        text = text.substr(0, maxlength) + "...";
      }
      return text.replace(/\n/g, "<br>");
    },

    percentDone: function (task) {
      var estimate = parseInt(helpers.get(task, "data.estimate"));
      var remaining = parseInt(helpers.get(task, "data.remaining"));
      return (1 - remaining / estimate) * 100 || 0;
    },

    pointsQuot: function (task, sortval) {
      var estimate = parseInt(helpers.get(task, "data.estimate"));
      var remaining = parseInt(helpers.get(task, "data.remaining"));
      if (sortval) {
        return ("" + (remaining || estimate || "0")).pad(3);
      }
      if (!estimate || !remaining || estimate == remaining) {
        return estimate || remaining || "-";
      } else {
        return `${remaining}/${estimate}`;
      }
    },
    getTaskTableInner: function () {
      var self = this;
      return new Promise(function (resolve) {
        var tableBody = self.$gridContainer.find("tbody");
        if (
          tableBody.length &&
          !!self.$gridContainer.find("table.nwd").length == self.nwdMode
        ) {
          resolve(tableBody);
          return;
        }
        self.$gridContainer
          .html(
            self.templates[self.nwdMode ? "nwdTable" : "taskTable"]({
              self: self,
            })
          )
          .attachWidgets();
        var sortTable = self.$gridContainer.find(".sortable");
        require(["widgets/TableSort"], function (TableSort) {
          self.sorter = new TableSort(sortTable);
          resolve(sortTable.find("tbody"));
        });
      });
    },

    /*getAssignees: function(tasks) {
            var assignees = {};
            _.each(tasks, function(task) {
                var id = (task.assignee || {}).id;
                if(id) {
                    assignees[id] = assignees[id] || task.assignee;
                    assignees[id].taskCount = (assignees[id].taskCount || 0)+1
                }
            });
            return assignees;
        },*/

    filterTasks: function (tasks, filters) {
      if (!filters.length) {
        return tasks;
      }
      var collectedFilters = {};
      _.each(filters, function (filter) {
        if (filter) {
          let colFilter = collectedFilters[filter.field];
          if (colFilter) {
            if (!_.isObject(colFilter.value)) {
              var obj = {};
              obj[colFilter.value] = 1;
              colFilter.value = obj;
            }
            colFilter.value[filter.value] = 1;
          } else {
            collectedFilters[filter.field] = filter;
          }
        }
      });

      filters = _.values(collectedFilters);

      var output = [];
      _.each(tasks, function (task) {
        var ok = true;
        for (var idx = 0; idx < filters.length; idx++) {
          let filter = filters[idx];
          if (filter) {
            let value = helpers.get(task, filter.field);
            if (
              _.isObject(filter.value)
                ? !(value in filter.value)
                : value != filter.value
            ) {
              ok = false;
              break;
            }
          }
        }
        if (ok) {
          output.push(task);
        }
      });
      return output;
    },

    updateCounts: function (tasks) {
      // get the count of own and context tasks
      var self = this;
      var pageFilter = [];
      if (dit.submission_id) {
        pageFilter = [
          { field: "content_type", value: "submission" },
          { field: "model_id", value: dit.submission_id },
        ];
      } else {
        if (dit.organisation_id) {
          pageFilter = [
            { field: "content_type", value: "organisation" },
            { field: "model_id", value: dit.organisation_id },
          ];
        }
        if (dit.page == "actions") {
          var stateId = JSON.parse($("#state-json").val() || "{}").id;
          var actionKey = location.hash.replace("#", "");
          pageFilter = [
            { field: "content_type", value: "case workflow" },
            { field: "model_id", value: stateId },
            { field: "model_key", value: actionKey },
          ];
        }
        if (dit.page in { parties: 1, submissions: 1, case_page: 1 }) {
          pageFilter = [{ field: "model_key", value: dit.page }];
        }
        if (dit.content_type == "content.content") {
          pageFilter = [
            { field: "content_type", value: "content" },
            { field: "model_id", value: dit.model_id },
          ];
        }
      }
      this.filters = this.filters || {};
      this.filters["page"] = pageFilter;
      this.filters["own"] = [{ field: "assignee.id", value: dit.user_id }];

      this.el.find(".counts .task-count").each(function () {
        var $el = $(this);
        var key = $el.attr("data-key");
        var filter = self.filters[key];
        if (filter && filter.length) {
          var count = self.filterTasks(tasks, filter).length;
        }
        $el.find("span").text(count || 0);
        $el.setClass("selected", self.controller.activeFilters[key]);
      });
    },

    renderTaskList: function () {
      var self = this;
      var modeSplit = /(^[^\-]+)(?:-(.*))?$/.exec(
        self.controller.settings.listMode
      ) || ["", "table"];
      self.listMode = modeSplit[1];
      self.nwdMode = self.listMode == "nwds";
      taskData[self.nwdMode ? "getNwd" : "getTaskList"]
        .call(self, self.listMode)
        .then(function (tasks) {
          //self.assignees = self.getAssignees(tasks);
          self.updateCounts(tasks);
          self.renderCaseFilter(tasks);
          var renderFilters = [];
          _.each(self.controller.activeFilters, function (val, filterKey) {
            renderFilters = renderFilters.concat(self.filters[filterKey]);
          });
          tasks = self.filterTasks(tasks, renderFilters) || [];
          tasks.sort(sortFn("due_date"));
          switch (self.listMode) {
            case "table":
            case "nwds":
              var templateName = self.nwdMode
                ? "nwdListInner"
                : "taskListInner";
              self.getTaskTableInner().then(function (tableBody) {
                tableBody.html(
                  self.templates[templateName]({ tasks: tasks, self: self })
                );
                var sortSettings =
                  helpers.get(self, "controller.settings.sort") || {};
                self.sorter.sortTable(
                  sortSettings.colIndex,
                  sortSettings.direction
                );
              });
              break;
            case "card":
              self.$gridContainer.html(
                self.templates["taskCardView"]({ tasks: tasks, self: self })
              );
              break;
            case "calendar":
              require(["widgets/tasks/ResourceView"], function (ResourceView) {
                self.resourceView =
                  self.resourceView ||
                  new ResourceView(self.controller, self.$gridContainer);
                self.resourceView.renderCalendar(tasks);
              });
              break;
          }
        });
    },
    renderCaseFilter: function (tasks) {
      var self = this;
      var caseIndex = helpers.index(tasks, "case.reference");
      var cases = [];
      _.each(caseIndex, function (tasks, ref) {
        if (ref) {
          // exclude non-case tasks
          self.filters[ref] = {
            value: ref,
            field: "case.reference",
          };
          cases.push({
            reference: ref,
            taskCount: tasks.length,
          });
        }
      });
      self.controller.el
        .find(".case-filter")
        .html(self.templates["caseFilter"]({ cases: cases, self: self }));
    },
  };

  return constructor;
});
